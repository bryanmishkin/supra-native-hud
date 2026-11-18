#!/usr/bin/env python3
"""Targeted factory PiP exploration. No drawing, subscriptions or startup writes."""
import argparse, hashlib, json, time
from pathlib import Path
import capture_runtime as runtime
from consolidated_capture import Session, save
from capture_output_driver import snapshot, BASELINE
from collect_pip_router import CONTROL
from audit_pip_binding import audit

PHASES=('original','hud-nav-off','hud-nav-on','restored')
HOLDS=(20,20,30,10)
COMMANDS=(('surface',CONTROL+'get surface 1056'),
          ('screen0',CONTROL+'get screen 0'),('screen1',CONTROL+'get screen 1'),
          ('display1','cat /dev/screen/0/dpy-1'),('display2','cat /dev/screen/0/dpy-2'))

def verify(root, recording):
    failures=[]
    result=json.loads((recording/'result.json').read_text())
    if not result.get('capture_valid'): failures.append('capture invalid')
    if not result.get('cleanup_verified'): failures.append('recorder cleanup unverified')
    clock=result.get('clock_sample',{})
    if not clock.get('valid_numeric_epoch'):failures.append('clock sample unavailable')
    data=(recording/'traffic.pcap').read_bytes()
    if hashlib.sha256(data).hexdigest()!=result.get('sha256'):failures.append('pcap hash mismatch')
    rows=[]
    for phase in PHASES:
        p=root/(phase+'.json')
        if not p.exists():failures.append('missing phase '+phase);continue
        row=json.loads(p.read_text());rows.append(row)
        if row.get('phase')!=phase or not row.get('observation'):failures.append('invalid phase '+phase)
        if not row.get('snapshots_ok'):failures.append('snapshot failure '+phase)
        for command in row.get('commands',[]):
            saved=root/('snapshot-'+phase)/(command['name']+'.txt')
            if not saved.exists() or hashlib.sha256(saved.read_bytes()).hexdigest()!=command['sha256']:failures.append('snapshot hash mismatch '+phase)
    start=result.get('ready_seen_epoch',float('inf'))
    end=result.get('host_start_epoch',0)+result.get('stats',{}).get('elapsed_s',0)
    if len(rows)==4:
        times=[r['host_epoch'] for r in rows]+[end]
        for i,phase in enumerate(PHASES):
            if not start<=times[i]<=end or times[i+1]-times[i]<HOLDS[i]:failures.append('insufficient capture coverage '+phase)
    for label in ('v1-before','v1-after'):
        p=root/(label+'.json')
        if not p.exists() or not json.loads(p.read_text()).get('all_15_match'):failures.append(label+' hashes not verified')
    analysis=audit(recording/'traffic.pcap')
    save(root/'pixel-binding.json',analysis)
    if analysis['errors']:failures.append('pixel-binding decoder errors')
    report={'technical_capture_complete':not failures,'failures':failures,
            'phases':rows,'recording':str(recording.resolve()),
            'owner_final_check_required':True,'larger_pixels_proven':False,
            'interpretation':'Compare B009 selection and B006 native-image references across phase times. ACKs do not prove windshield pixels.',
            'clock_sample':clock}
    save(root/'exploration-result.json',report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('plan','before','phase','after','verify'))
    p.add_argument('--execute',action='store_true')
    for n in ('head','local'):p.add_argument('--'+n,type=runtime.link_local)
    for n in ('known-hosts','socket','output','recording'):p.add_argument('--'+n,type=Path)
    p.add_argument('--phase',choices=PHASES);p.add_argument('--observation')
    a=p.parse_args()
    if a.action=='plan':
        print(json.dumps({'phases':dict(zip(PHASES,HOLDS)),'recorder_seconds':120,'drawing':False,'V1':'remains running; installed hashes checked before/after','menu':'normal factory HUD navigation option only; absent option means skip'},indent=2));return 0
    if not a.output:p.error('--output required')
    if a.action=='verify':
        if not a.recording:p.error('--recording required')
        r=verify(a.output,a.recording);print(json.dumps(r,indent=2));return 0 if r['technical_capture_complete'] else 2
    if not a.execute or not all((a.head,a.local,a.known_hosts)):p.error('Remote reads require --execute and verified SSH addresses/known-hosts')
    if a.action=='phase':
        if not all((a.recording,a.phase,a.observation)):p.error('Phase, recording and actual owner observation required')
        state=json.loads((a.recording/'status.json').read_text());now=time.time()
        if (a.recording/'result.json').exists() or not 0<=now-state['ready_seen_epoch']<110:p.error('Recorder is not active with sufficient remaining time')
        dest=a.output/(a.phase+'.json')
        if dest.exists():p.error('Phase already recorded; use a fresh run rather than overwrite evidence')
        row={'phase':a.phase,'host_epoch':now,'observation':a.observation,'snapshots_ok':False,'commands':[]}
        save(dest,row)
        # Separate manifests prevent overwriting the recorder manifest.
        a.output=a.output/('snapshot-'+a.phase);s=Session(a);s.identity()
        for name,cmd in COMMANDS:
            before=time.time();r=s.call(cmd,timeout=5);after=time.time()
            (s.root/(name+'.txt')).write_bytes(r.stdout)
            ok=r.returncode==0 and bool(r.stdout.strip())
            row['commands_ok']=row.get('commands_ok',True) and ok
            row['commands'].append({'name':name,'host_before':before,'host_after':after,'exit':r.returncode,'sha256':hashlib.sha256(r.stdout).hexdigest()})
            save(dest,row)
        row['snapshots_ok']=row.get('commands_ok',False) and len(row['commands'])==len(COMMANDS)
        save(dest,row)
        return 0 if row['snapshots_ok'] else 2
    s=Session(a);s.identity()
    r=snapshot(s,'v1-'+a.action,json.loads(BASELINE.read_text())['component_sha256'])
    s.persist();return 0 if r['all_15_match'] else 2
if __name__=='__main__':raise SystemExit(main())
