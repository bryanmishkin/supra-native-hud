#!/usr/bin/env python3
"""Bounded high-guidance bitmap experiment; offline unless explicitly executed.

No V1 file writes, instance disposal, PiP output, RPM polling or Hz tests.
The two cases isolate the current-state close-guidance threshold.
"""
import argparse,hashlib,ipaddress,json,signal,socket,struct,subprocess,time
from pathlib import Path
from b006_high_bitmap import build_candidate
from ric_shared_trial import SharedDrawingTrial,SharedSession,allocation_from_reply
from ric_live_trial import TcpExchange
from ric_graph import decode_graph_body
from ric_rle32 import encode_bgra,marker_bgra
from verify_current_v1_test_baseline import verify as verify_v1

# Native sender fields, paired difference and cleanup reviewed.
# This admits a bounded placement experiment, not a proven larger surface.
LIVE_READY=True

def plain(value):
    if isinstance(value,bytes):return value.hex()
    if isinstance(value,dict):return {k:plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [plain(v) for v in value]
    return value

def v1_stopped(base,destination):
    command="grep -q '^STOPPED$' /tmp/supra-hud-v1/resident.status && test ! -e /tmp/supra-hud-v1/factory.sock && test ! -e /tmp/supra-hud-v1/active.jsonl.handoff"
    r=subprocess.run(base+[destination,command],capture_output=True,timeout=5)
    if r.returncode:raise RuntimeError('V1 is not confirmed cleanly stopped; no test permitted')

class HighTrial(SharedDrawingTrial):
    def __init__(self,session,candidate,record,observe,cleanup):
        super().__init__(session,record,observe,cleanup)
        self.candidate=candidate
    def send(self,method,body):
        if method==11:
            for m,b in self.candidate['setup'][:3]:super().send(m,b)
            return
        if method==10 and body[8]==15:body=self.candidate['setup'][3][1]
        super().send(method,body)
        if method==9 and body[8]==33 and decode_graph_body(method,body)['list_state']['guidance_state']==2:
            super().send(9,self.candidate['position_start'])
    def withdraw(self):
        super().withdraw()
        if not self.graph_started:return
        row=dict(method=9,role='restore stopped destination information',acknowledged=False)
        self.result['cleanup_steps'].append(row)
        try:self.session._empty(9,self.candidate['position_stop']);row['acknowledged']=True
        except Exception as e:row['error']=str(e)
        self.save()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--case',choices=['control','close'],default='close')
    p.add_argument('--create-response',type=Path)
    p.add_argument('--support-profile',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--ssh-socket',type=Path)
    p.add_argument('--v1-pre',type=Path,help='Fresh read-only capture of all 15 current V1 files')
    p.add_argument('--head')
    p.add_argument('--guidance-stopped',action='store_true')
    a=p.parse_args()
    if a.execute and not LIVE_READY:p.error('Native threshold verification/review pending; offline plans only')
    if not any((a.create_response,a.support_profile,a.output)):
        print('Offline plan: paired 30-second high-picture tests, 92m control versus 1000m threshold, same 150x36 inline bitmap, no road-icon binding. V1 remains installed.');return 0
    if not all((a.create_response,a.support_profile,a.output)):p.error('Plan requires create response, support profile and new output directory')
    allocation=allocation_from_reply(a.create_response.read_bytes()[16:])
    candidate=build_candidate(a.support_profile.read_bytes(),allocation,threshold=92.0 if a.case=='control' else 1000.0)
    raw=marker_bgra(150,36)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'marker.bgra').write_bytes(raw)
    (a.output/'plan.json').write_text(json.dumps(dict(case=a.case,seconds=30,marker_sha256=hashlib.sha256(raw).hexdigest(),candidate=plain(candidate),v1_modified=False),indent=2))
    if not a.execute:print('Offline plan written; no vehicle connection.');return 0
    if not(a.ssh_socket and a.head and a.guidance_stopped and a.v1_pre):p.error('Execution requires verified SSH master, current V1 pre-capture and stopped guidance/radio')
    baseline=verify_v1(a.v1_pre)
    (a.output/'v1-preverified.json').write_text(json.dumps(baseline,indent=2))
    ipaddress.IPv4Address(a.head)
    base=['ssh','-S',str(a.ssh_socket.resolve()),'-o','BatchMode=yes','-o','ConnectTimeout=3']
    destination='root@'+a.head
    v1_stopped(base,destination)
    with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
    forward=f'127.0.0.1:{port}:160.48.199.96:30502'
    r=subprocess.run(base+['-O','forward','-L',forward,destination],capture_output=True,timeout=5)
    if r.returncode:raise RuntimeError('Could not open owned forwarding channel')
    report={}
    def record(value):
        value['case']=a.case;value['threshold']=candidate['threshold'];value['larger_extent_proven']=False
        tmp=a.output/'result.tmp';tmp.write_text(json.dumps(value,indent=2));tmp.replace(a.output/'result.json')
    def cleanup():
        signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
    def stop(sig,frame):raise KeyboardInterrupt()
    def observe(phase,seconds):
        print(f'WATCH NOW: {a.case} high-picture marker, full 30 seconds. Keep navigation/radio closed.',flush=True)
        end=time.monotonic()+30
        while time.monotonic()<end:time.sleep(min(.2,max(0,end-time.monotonic())))
        return None
    class BitmapSession(SharedSession):
        def upload_marker(self):
            self.upload_bitmap(allocation['resource_id'],allocation['resource_type'],[150,36],encode_bgra(raw))
    signal.signal(signal.SIGTERM,stop)
    try:
        with socket.create_connection(('127.0.0.1',port),2) as sock:
            session=BitmapSession(TcpExchange(sock,a.output),allocation)
            report=HighTrial(session,candidate,record,observe,cleanup).run()
    finally:
        try:
            r=subprocess.run(base+['-O','cancel','-L',forward,destination],capture_output=True,timeout=5)
            report['forward_cancelled']=r.returncode==0
        except Exception as e:report['forward_cancelled']=False;report['forward_error']=str(e)
        record(report)
    steps=report.get('cleanup_steps',[]);resources=report.get('cleanup',{}).get('resources',[])
    ok=bool(steps and resources and report.get('forward_cancelled') and
        all(x.get('acknowledged') is True for x in steps) and
        all(x.get('dispose_acknowledged') is True and x.get('post_dispose_check') is False for x in resources))
    print(json.dumps(dict(cleanup_verified=ok,visual_confirmation_required=True,v1_restore_required=True)))
    return 0 if ok else 2
if __name__=='__main__':raise SystemExit(main())
