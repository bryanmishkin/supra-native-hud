#!/usr/bin/env python3
"""Resumable road-image batch with visual gates and final V1 verification."""
import argparse,json,subprocess,sys,time
from pathlib import Path
from run_hud_selection_session import Session as BaseSession,save,digest,advancing,last_frame,output_empty,V1,RAM
from road_list_expansion_trial import profile_commands
from prepare_road_list_expansion import limits
from verify_current_v1_test_baseline import verify
CASES=('control','two_icons_one_entry','one_icon_two_entries')
TOOLS=Path(__file__).resolve().parent
SOURCES=('manage_road_list_session.py','run_road_list_expansion.py','road_list_expansion_trial.py','ric_road_list.py','prepare_road_list_expansion.py')

def audit(root):
    state=json.loads((root/'state.json').read_text());missing=[]
    for c in CASES:
        row=state.get(c,{})
        if not row.get('passed'):missing.append(c+': protocol completion')
        if not row.get('observation',{}).get('clear'):missing.append(c+': visual clearance')
    if not state.get('restoration',{}).get('verified'):missing.append('V1 restoration/runtime verification')
    return dict(complete=not missing,missing=missing,observations={c:state.get(c,{}).get('observation')for c in CASES})

class Session(BaseSession):
    def __init__(self,a):
        kit=json.loads((a.output/'kit.json').read_text())
        for name,sha in kit['source_sha256'].items():
            if digest(TOOLS/name)!=sha:raise ValueError('Prepared source changed; rebuild kit: '+name)
        super().__init__(a)
    def pause(self):
        if self.state.get('paused'):raise ValueError('Already paused')
        self.files('pre');self.snapshot('before')
        stopped=self.remote('cat '+RAM+'/resident.status').strip()==b'STOPPED'
        if not stopped:
            (self.root/'stop-v1.txt').write_bytes(self.remote(V1+'/supra-resident-qnx --stop '+RAM,35))
        self.quiet();self.snapshot('paused');self.state['paused']=True;self.commit()
        print('V1 is stopped; confirm clear displays before control.')
    def case(self):
        a=self.a;c=a.case
        if not c or c in self.state:raise ValueError('New named case required; never overwrite attempts')
        if not(self.state.get('paused')and a.displays_clear and a.guidance_closed):raise ValueError('Paused and visually clear, with overlays closed, required')
        index=CASES.index(c)
        if index:
            prior=self.state.get(CASES[index-1],{})
            if not prior.get('passed') or not prior.get('observation',{}).get('clear'):raise ValueError('Prior case/visual cleanup incomplete')
            control=self.state.get('control',{}).get('observation',{})
            if not control.get('windshield_images',0):raise ValueError('Working windshield control not confirmed')
        self.quiet();verify(self.root/'pre')
        row=dict(started=time.time(),passed=False);self.state[c]=row;self.commit()
        cmd=[sys.executable,str(TOOLS/'run_road_list_expansion.py'),'--case',c,'--create-reply',str(self.root/'create-response.bin'),'--support-profile',str(self.root/'supra-profile.bin'),'--output',str(self.root/c),'--execute','--ssh-socket',a.ssh_socket,'--head','169.254.199.119','--parked-overlays-closed-displays-clear']
        try:
            child=subprocess.Popen(cmd);row['pid']=child.pid;self.commit()
            try:code=child.wait(timeout=180)
            except (subprocess.TimeoutExpired,KeyboardInterrupt):
                child.terminate()
                try:child.wait(timeout=45)
                except subprocess.TimeoutExpired:row['cleanup_process_unconfirmed']=True
                raise
            row['exit_code']=code
            result=json.loads((self.root/c/'result.json').read_text())
            row['passed']=code==0 and result.get('status')=='window_finished' and result.get('protocol_cleanup_passed') is True and result.get('forward_removed') is True and not result.get('recording_errors')
        finally:self.commit()
        if not row['passed']:raise RuntimeError('Case incomplete; no next case admitted. Preserve result and recover.')
        print('Protocol cleanup passed. Record separate windshield/cluster observations and visual clearance.')
    def finalize(self):
        if not self.a.v1_visible:raise ValueError('Owner confirmation of updating V1 after normal restart required')
        if any(c in self.state and not self.state[c].get('observation',{}).get('clear')for c in CASES):raise ValueError('Attempted tests need visual clearance before final verification')
        label='post-'+str(time.time_ns());self.files(label);frames=[];heartbeats=[]
        for i in range(2):
            raw=self.remote('cat '+RAM+'/acceptance.json');(self.root/(label+'-health'+str(i)+'.json')).write_bytes(raw);h=json.loads(raw)
            if not(h.get('worker_running')is True and h.get('available')is True and h.get('quarantined')is False):raise ValueError('V1 supervisor unhealthy')
            frames.append(last_frame(self.remote('tail -100 '+RAM+'/active.jsonl')))
            heartbeats.append(int(self.remote('cat '+RAM+'/heartbeat')));self.snapshot(label+'-'+str(i))
            if not i:time.sleep(3)
        if not advancing(*frames)or heartbeats[1]<=heartbeats[0]:raise ValueError('V1 frames/samples/heartbeat not advancing')
        if not output_empty(self.remote('cat /dev/screen/0/dpy-2')):raise ValueError('Secondary output not empty')
        if self.remote('cat '+V1+'/enabled && test ! -e '+V1+'/disabled').strip()!=b'SUPRA-PERSISTENT-1':raise ValueError('V1 enable/lockout check failed')
        self.state['paused']=False
        self.state['restoration']=dict(verified=True,files=label,frames=frames,heartbeat=heartbeats,owner_visible=True,epoch=time.time());self.commit()
        save(self.root/'completeness.json',audit(self.root));print(json.dumps(audit(self.root),indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','pause','case','observe','finalize','audit'])
    p.add_argument('--output',type=Path,required=True);p.add_argument('--create-reply',type=Path);p.add_argument('--support-profile',type=Path)
    p.add_argument('--execute',action='store_true');p.add_argument('--ssh-socket');p.add_argument('--case',choices=CASES)
    p.add_argument('--displays-clear',action='store_true');p.add_argument('--guidance-closed',action='store_true');p.add_argument('--v1-visible',action='store_true')
    p.add_argument('--windshield-images',type=int,choices=[0,1,2]);p.add_argument('--cluster-images',type=int,choices=[0,1,2]);p.add_argument('--arrangement',choices=['none','single','side-by-side','stacked','overlap','clipped','other']);p.add_argument('--note',default='')
    a=p.parse_args()
    if a.command=='prepare':
        if not(a.create_reply and a.support_profile):p.error('Create reply and accepted support profile required')
        reply=a.create_reply.read_bytes();profile=a.support_profile.read_bytes();config=limits(reply)
        plans={c:profile_commands(profile,c)for c in CASES};a.output.mkdir(parents=True,exist_ok=False)
        (a.output/'create-response.bin').write_bytes(reply);(a.output/'supra-profile.bin').write_bytes(profile)
        for c,(start,stop)in plans.items():save(a.output/(c+'-plan.json'),dict(setup=[(m,b.hex())for m,b in start],cleanup=[(m,b.hex())for m,b in stop]))
        save(a.output/'kit.json',dict(sha256={f.name:digest(f)for f in a.output.iterdir()},source_sha256={n:digest(TOOLS/n)for n in SOURCES},cases=list(CASES),visible_seconds=30,limits=config,no_hz_tests=True,v1_writes=False))
        save(a.output/'state.json',dict(paused=False,prepared_epoch=time.time()));print('Prepared all three cases offline. No vehicle connection.');return
    if a.command=='audit':print(json.dumps(audit(a.output),indent=2));return
    s=Session(a)
    if a.command=='observe':
        if not a.case or not s.state.get(a.case,{}).get('passed'):p.error('Completed case required')
        if a.windshield_images is None or a.cluster_images is None or a.arrangement is None:p.error('Separate image counts and arrangement required')
        s.state[a.case]['observation']=dict(windshield_images=a.windshield_images,cluster_images=a.cluster_images,arrangement=a.arrangement,clear=a.displays_clear,note=a.note,epoch=time.time());s.commit()
    else:getattr(s,a.command)()
if __name__=='__main__':main()
