#!/usr/bin/env python3
"""Resumable, RAM-only paired canvas session. prepare/audit are entirely offline.

Known-negative distance pair: new pause/case runs additionally require
--repeat-known-negative-control. This is not a larger-HUD fix.
Live phases require --execute and an existing verified SSH master. No SSH
activation, reboot, persistent-file writes, lockout clearing, or Hz tests.
"""
import argparse
import hashlib
import json
import re
import shlex
import socket
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path
from verify_current_v1_test_baseline import contract, verify
from run_corrected_pip_trial import plan, descriptor, steps, withdrawal

TOOLS = Path(__file__).resolve().parent
CASES = ('control461', 'contrast69')
MARKER_SHA = '2546bcc83ce396ec3c67df3b5cac8333a9a1f79009b8bb54e06251633efc1753'
CAPTURE_SHA = 'fc0ee3c1c275ba75dd3ee64402e5b4747d5e7a3454e34c1c318d83df2e045ea6'
V1 = '/var/opt/supra-hud/v1'
RAM = '/tmp/supra-hud-v1'

def save(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def capture_valid(data, text):
    rows = [json.loads(x) for x in text.splitlines() if x.startswith('{')]
    if not rows or rows[0].get('ready') is not True or rows[0].get('duration_s') != 120:
        return False
    s = rows[-1]
    if not (s.get('reason') == 'duration' and s.get('elapsed_s', 0) >= 119.5
            and s.get('drops') == 0 and s.get('interface_drops') == 0
            and s.get('packets', 0) > 0 and s.get('pcap_bytes') == len(data)):
        return False
    if len(data) < 24 or data[:4] != b'\xd4\xc3\xb2\xa1':
        return False
    off = 24; count = 0
    while off < len(data):
        if off + 16 > len(data): return False
        _, _, size, original = struct.unpack_from('<IIII', data, off)
        if size > original or size > 65535 or off + 16 + size > len(data): return False
        off += 16 + size; count += 1
    return count == s['packets']

def last_frame(raw):
    rows=[]
    for line in raw.decode(errors='replace').splitlines():
        try: row=json.loads(line)
        except ValueError: continue
        if all(k in row for k in ('frame','sample_ms','rpm')): rows.append(row)
    if not rows: raise ValueError('No live drawing frame in runtime log')
    return rows[-1]

def advancing(first, second):
    return second['frame']>first['frame'] and second['sample_ms']>first['sample_ms']

def output_empty(raw):
    text=raw.decode(errors='replace')
    return ('device_id = OTHER2' in text and 'windows = (none)' in text
            and bool(re.search(r'^\s*source =',text,re.M))
            and all(x.strip()=='(none)' for x in re.findall(r'^\s*source = (.*)$',text,re.M)))

def cleanup_ok(r):
    return (r.get('status') == 'finished' and r.get('local_cleanup') is True
            and r.get('protocol_cleanup') is True and r.get('resource_absent') is True)

def audit(root):
    s = json.loads((root/'state.json').read_text())
    missing = []
    for c in CASES:
        r = root/c/'result.json'
        if not r.exists() or not cleanup_ok(json.loads(r.read_text())): missing.append(c+': completed trial/cleanup')
        if not s.get(c, {}).get('capture_valid'): missing.append(c+': complete zero-drop recording')
        if not s.get(c, {}).get('remote_removed'): missing.append(c+': RAM files removed')
        o = s.get(c, {}).get('observation', {})
        if not o.get('location') or o.get('displays_clear') is not True: missing.append(c+': visual observation/clearance')
    if not s.get('restoration', {}).get('verified'): missing.append('V1 files/runtime/visual restoration')
    return dict(complete=not missing, missing=missing, windshield_success=any(
        s.get(c, {}).get('observation', {}).get('location') in ('windshield', 'both') for c in CASES))

class Session:
    def __init__(self, a):
        self.a = a; self.root = a.output.resolve()
        self.state = json.loads((self.root/'state.json').read_text())
        self.kit = json.loads((self.root/'kit.json').read_text())
        for n,h in self.kit['sha256'].items():
            if digest(self.root/n) != h: raise ValueError('Kit changed: '+n)
        if a.command in ('audit','observe'): return
        if not a.execute: raise ValueError('Live phase requires --execute')
        if not a.ssh_socket or not Path(a.ssh_socket).is_socket(): raise ValueError('Existing verified SSH master required')
        self.ssh = ['ssh','-T','-S',a.ssh_socket,'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
                    '-o','ConnectTimeout=4','root@169.254.199.119']
        subprocess.run(self.ssh[:-1]+['-O','check',self.ssh[-1]], check=True, capture_output=True, timeout=5)
    def commit(self): save(self.root/'state.json',self.state)
    def remote(self, cmd, timeout=12, data=None):
        r = subprocess.run(self.ssh+[cmd], input=data, capture_output=True, timeout=timeout)
        if r.returncode: raise RuntimeError('Remote command failed: '+cmd+'\n'+r.stderr.decode(errors='replace'))
        return r.stdout
    def files(self, label):
        d = self.root/label; d.mkdir()
        for n,p in contract()[1].items(): (d/n).write_bytes(self.remote('cat '+shlex.quote(p)))
        save(self.root/(label+'-verified.json'),verify(d))
    def quiet(self):
        self.remote("test \"$(cat "+RAM+"/resident.status)\" = STOPPED && test ! -e "+RAM+"/factory.sock && test ! -e "+RAM+"/active.jsonl.handoff")
    def snapshot(self, label):
        for n,cmd in [('acceptance','cat '+RAM+'/acceptance.json'),('heartbeat','cat '+RAM+'/heartbeat'),
                      ('active','tail -100 '+RAM+'/active.jsonl'),('display','cat /dev/screen/0/dpy-2')]:
            (self.root/(label+'-'+n+'.txt')).write_bytes(self.remote(cmd))
    def pause(self):
        if self.state.get('paused'): raise ValueError('Already paused; do not repeat')
        self.files('pre'); self.snapshot('before')
        out=self.remote(V1+'/supra-resident-qnx --stop '+RAM,35)
        (self.root/'stop-v1.txt').write_bytes(out)
        self.quiet(); self.snapshot('paused')
        self.state['paused']=True; self.commit()
        print('V1 stopped. Confirm both displays clear before case control461; no restart yet.')
    def case(self):
        c=self.a.case
        if not self.state.get('paused') or not self.a.displays_clear or not self.a.guidance_closed:
            raise ValueError('Paused V1 and fresh visual/guidance/radio confirmation required')
        if c in self.state: raise ValueError('Case already attempted; preserve evidence, do not overwrite/retry')
        if c==CASES[1]:
            prior=self.state.get(CASES[0],{})
            if not prior.get('passed') or not prior.get('observation',{}).get('displays_clear'):
                raise ValueError('First case and visual cleanup must pass')
        self.quiet(); verify(self.root/'pre')
        if not output_empty(self.remote('cat /dev/screen/0/dpy-2')): raise ValueError('OTHER2 not empty')
        interface=self.remote('ifconfig vlan73').decode(errors='replace')
        if not re.search(r'\binet\s+160\.48\.199\.119\b',interface) or not re.search(r'<[^>]*\bUP\b',interface):
            raise ValueError('Internal interface not verified')
        run='/tmp/supra-pip-corrected-'+uuid.uuid4().hex[:16]
        rec=dict(remote=run,started_epoch=time.time(),passed=False)
        self.state[c]=rec; self.commit()
        cap=None; forward=None; made=False
        try:
            self.remote('umask 077; mkdir '+run); made=True
            for name in ('marker','capture'):
                raw=(self.root/name).read_bytes()
                self.remote('cat > '+run+'/'+name,data=raw)
                if self.remote('cat '+run+'/'+name)!=raw: raise ValueError('Readback mismatch '+name)
                self.remote('chmod 700 '+run+'/'+name)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
            forward='127.0.0.1:'+str(port)+':160.48.199.96:30502'
            subprocess.run(self.ssh[:-1]+['-O','forward','-L',forward,self.ssh[-1]],check=True,capture_output=True,timeout=5)
            for name,cmd in [('producer',run+'/marker --parked-experiment '+str(self.kit['description_id'])+' day '+run+' 160.48.199.119 160.48.199.96 30503 30490 --observe-hud-selection'),
                             ('go',': > '+run+'/go'),('stop',': > '+run+'/stop')]:
                save(self.root/(c+'-'+name+'.json'),self.ssh+[cmd])
            with (self.root/(c+'.pcap')).open('wb') as pout, (self.root/(c+'-capture.stderr')).open('wb') as err:
                cap=subprocess.Popen(self.ssh+[run+'/capture --capture vlan73'],stdout=pout,stderr=err)
                deadline=time.monotonic()+8
                while b'"ready":true' not in (self.root/(c+'-capture.stderr')).read_bytes():
                    if cap.poll() is not None or time.monotonic()>deadline: raise RuntimeError('Recorder not ready')
                    time.sleep(.1)
                rec['capture_ready_epoch']=time.time(); self.commit()
                self.snapshot(c+'-before')
                args=[sys.executable,str(TOOLS/'run_corrected_pip_trial.py'),'--create-response',str(self.root/'create-response.bin'),
                      '--support-profile',str(self.root/'supra-profile.bin'),'--style','day','--distance',str(461 if c==CASES[0] else 69),
                      '--output',str(self.root/c),'--observe-hud-selection','--execute','--v1-pre',str(self.root/'pre'),
                      '--v1-paused-and-displays-clear','--guidance-stopped','--local-port',str(port)]
                for name in ('producer','go','stop'): args += ['--'+name+'-argv',str(self.root/(c+'-'+name+'.json'))]
                result=subprocess.run(args,timeout=100)
                rec['trial_finished_epoch']=time.time(); rec['trial_exit']=result.returncode; self.commit()
                self.snapshot(c+'-after')
                if cap.poll() is not None: raise RuntimeError('Recorder ended before post-test snapshot')
                print('Marker window ended; recorder is finishing its bounded 120-second window.',flush=True)
                cap.wait(timeout=130)
            rec['capture_valid']=cap.returncode==0 and capture_valid((self.root/(c+'.pcap')).read_bytes(),(self.root/(c+'-capture.stderr')).read_text())
            r=json.loads((self.root/c/'result.json').read_text())
            rec['passed']=result.returncode==0 and cleanup_ok(r) and rec['capture_valid']
        except (Exception,KeyboardInterrupt) as e:
            rec['error']=str(e) or type(e).__name__
        finally:
            # The native helper has its own 45-second bound; never kill factory processes.
            if made:
                try: self.remote(': > '+run+'/stop')
                except Exception as e: rec['stop_error']=str(e)
            if cap is not None and cap.poll() is None:
                try: cap.wait(timeout=135)
                except subprocess.TimeoutExpired: cap.kill(); cap.wait(); rec['capture_valid']=False
            if forward:
                try: subprocess.run(self.ssh[:-1]+['-O','cancel','-L',forward,self.ssh[-1]],capture_output=True,timeout=5)
                except Exception as e: rec['forward_cancel_error']=str(e)
            if made:
                try:
                    rpath=self.root/c/'result.json'
                    r=json.loads(rpath.read_text()) if rpath.exists() else {}
                    if cleanup_ok(r):
                        self.remote('rm -f '+run+'/marker '+run+'/capture '+run+'/go '+run+'/stop; rm -r '+run+' && test ! -e '+run)
                        rec['remote_removed']=True
                    else: rec['remote_removed']=False
                except Exception as e: rec['cleanup_error']=str(e)
            rec['passed']=rec.get('passed',False) and rec.get('remote_removed',False)
            self.commit()
        if not rec['passed']: raise RuntimeError('Case failed: preserve evidence; no next case. Restore V1 with final verification.')
        print('Protocol cleanup passed. Record marker location and visual clearance with observe.')
    def finalize(self):
        if not self.a.v1_visible: raise ValueError('Owner must confirm V1 visible and updating after normal restart')
        # Unique attempt directory permits diagnosis/retry without overwriting failed evidence.
        label='post-'+str(time.time_ns()); self.files(label)
        healthy=[]; frames=[]
        for i in range(2):
            raw=self.remote('cat '+RAM+'/acceptance.json'); (self.root/(label+'-health'+str(i)+'.json')).write_bytes(raw)
            h=json.loads(raw)
            if not (h.get('worker_running') is True and h.get('available') is True and h.get('quarantined') is False):
                raise ValueError('V1 supervisor is not healthy')
            frames.append(last_frame(self.remote('tail -100 '+RAM+'/active.jsonl')))
            heartbeat=int(self.remote('cat '+RAM+'/heartbeat').strip()); healthy.append(heartbeat)
            self.snapshot(label+'-'+str(i))
            if not i: time.sleep(3)
        if not advancing(frames[0],frames[1]): raise ValueError('Drawing frames / RPM samples did not advance')
        if healthy[1]<=healthy[0]: raise ValueError('V1 heartbeat did not advance')
        if not output_empty(self.remote('cat /dev/screen/0/dpy-2')): raise ValueError('OTHER2 retains a window/source')
        token=self.remote('cat '+V1+'/enabled && test ! -e '+V1+'/disabled')
        if token.strip()!=b'SUPRA-PERSISTENT-1': raise ValueError('Unexpected enable token')
        for c in CASES:
            if c in self.state: self.remote('test ! -e '+self.state[c]['remote'])
        self.state['restoration']=dict(verified=True,files=label,heartbeat=healthy,frames=frames,owner_visible=True,epoch=time.time())
        self.commit(); save(self.root/'completeness.json',audit(self.root))
        print(json.dumps(audit(self.root),indent=2))

def prepare(a):
    root=a.output.resolve(); root.mkdir(parents=True,exist_ok=False)
    for name,src in [('marker',a.marker),('capture',a.capture),('create-response.bin',a.create_response),('supra-profile.bin',a.support_profile)]:
        if not src: raise ValueError('All four prepared inputs required')
        (root/name).write_bytes(src.read_bytes())
    if digest(root/'capture')!=CAPTURE_SHA: raise ValueError('Recorder differs from proven 120-second build')
    if digest(root/'marker') != MARKER_SHA: raise ValueError('Wrong marker build')
    plans=[]
    for c,d in zip(CASES,(461,69)):
        p=plan((root/'create-response.bin').read_bytes(),(root/'supra-profile.bin').read_bytes(),'day',d)
        p['allow_hud_candidate']=True
        row=dict(allocation=p,descriptor=descriptor(p).hex(),steps=[(m,b.hex())for m,b in steps(p)],withdrawal=[(m,b.hex())for m,b in withdrawal(p)])
        save(root/(c+'-plan.json'),row); plans.append(row)
    if plans[0]['descriptor']!=plans[1]['descriptor'] or plans[0]['withdrawal']!=plans[1]['withdrawal']:
        raise ValueError('Pair changed image descriptor or cleanup')
    save(root/'kit.json',dict(schema=1,description_id=plans[0]['allocation']['models'][15],
        sha256={p.name:digest(p)for p in root.iterdir() if p.is_file()},cases=list(CASES),visible_seconds=30,
        recording_seconds_per_case=120,no_hz_tests=True,v1_writes=False))
    save(root/'state.json',dict(prepared_epoch=time.time(),paused=False))
    print('Offline kit prepared. No vehicle connection.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare','pause','case','observe','finalize','audit'])
    p.add_argument('--output',required=True,type=Path)
    for n in ('marker','capture','create-response','support-profile'): p.add_argument('--'+n,type=Path)
    p.add_argument('--execute',action='store_true'); p.add_argument('--ssh-socket')
    p.add_argument('--case',choices=CASES); p.add_argument('--displays-clear',action='store_true')
    p.add_argument('--guidance-closed',action='store_true'); p.add_argument('--v1-visible',action='store_true')
    p.add_argument('--location',choices=['windshield','cluster','both','factory-symbol-only','none'])
    p.add_argument('--note',default='')
    p.add_argument('--repeat-known-negative-control',action='store_true',
                   help='Explicitly repeat the cluster-only 20 November control; not a new HUD fix')
    a=p.parse_args()
    if a.command in ('pause','case') and not a.repeat_known_negative_control:
        p.error('Retired distance pair: both cases rendered cluster-only. New live runs require --repeat-known-negative-control; restoration and audit remain available.')
    if a.command=='prepare': prepare(a); return
    if a.command=='audit': print(json.dumps(audit(a.output),indent=2)); return
    s=Session(a)
    if a.command=='observe':
        if not a.case or a.case not in s.state or not a.location: p.error('Attempted case and location required')
        if 'capture_valid' not in s.state[a.case]: p.error('Wait for case recording to finish before recording observation')
        s.state[a.case]['observation']=dict(location=a.location,displays_clear=a.displays_clear,note=a.note,epoch=time.time()); s.commit()
    elif a.command=='case':
        if not a.case: p.error('--case required')
        s.case()
    else: getattr(s,a.command)()

if __name__=='__main__': main()
