#!/usr/bin/env python3
"""30-second structural road-image experiment. Offline by default; no V1 writes."""
import argparse,ipaddress,json,signal,socket,subprocess,time
from pathlib import Path
from road_list_expansion_trial import profile_commands,run
from prepare_road_list_expansion import limits
from ric_shared_trial import SharedSession,allocation_from_reply
from ric_live_trial import TcpExchange
from verify_current_v1_test_baseline import contract,verify


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=['control','two_icons_one_entry','one_icon_two_entries','right_boundary_ruler'],required=True)
    p.add_argument('--create-reply',type=Path,required=True);p.add_argument('--support-profile',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true')
    p.add_argument('--ssh-socket',type=Path);p.add_argument('--head');p.add_argument('--parked-overlays-closed-displays-clear',action='store_true')
    a=p.parse_args();reply=a.create_reply.read_bytes();profile=a.support_profile.read_bytes()
    config=limits(reply);setup,cleanup=profile_commands(profile,a.case);allocation=allocation_from_reply(reply[16:])
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'plan.json').write_text(json.dumps(dict(case=a.case,seconds=30,limits=config,
        setup=[dict(method=m,body_hex=b.hex())for m,b in setup],cleanup=[dict(method=m,body_hex=b.hex())for m,b in cleanup],
        larger_area_proven=False,v1_writes=False),indent=2))
    if not a.execute:print('Offline plan saved. No vehicle connection.');return 0
    if not(a.ssh_socket and a.head and a.parked_overlays_closed_displays_clear):p.error('Live run needs verified SSH master and parked, clear displays, closed factory overlays')
    ipaddress.IPv4Address(a.head)
    if not a.ssh_socket.is_socket():raise ValueError('Existing verified SSH master required')
    base=['ssh','-S',str(a.ssh_socket.resolve()),'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=3'];destination='root@'+a.head
    subprocess.run(base+['-O','check',destination],check=True,capture_output=True,timeout=5)
    def command(cmd):
        r=subprocess.run(base+[destination,cmd],capture_output=True,timeout=5)
        if r.returncode:raise RuntimeError('Read-only admission command failed')
        return r.stdout
    pre=a.output/'v1-pre';pre.mkdir()
    _,paths=contract()
    for name,path in paths.items():(pre/name).write_bytes(command('cat '+path))
    verify(pre)
    command("grep -q '^STOPPED$' /tmp/supra-hud-v1/resident.status && test ! -e /tmp/supra-hud-v1/factory.sock && test ! -e /tmp/supra-hud-v1/active.jsonl.handoff")
    with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
    forward=f'127.0.0.1:{port}:160.48.199.96:30502'
    result={};forward_attempted=False
    def record(r):
        tmp=a.output/'result.tmp';tmp.write_text(json.dumps(r,indent=2));tmp.replace(a.output/'result.json')
    def cancel(*_):raise KeyboardInterrupt('Operator cancellation')
    def begin_cleanup():
        signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN)
    def observe(seconds):
        print(f'WATCH NOW: {a.case}, static markers, full30seconds. Inspect windshield and cluster.',flush=True)
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            time.sleep(min(1,max(0,end-time.monotonic())))
            for rid in session.resources:
                if not session._check(rid,1):raise RuntimeError('Marker resource disappeared during observation')
    try:
        signal.signal(signal.SIGINT,cancel);signal.signal(signal.SIGTERM,cancel)
        forward_attempted=True
        subprocess.run(base+['-O','forward','-L',forward,destination],check=True,capture_output=True,timeout=5)
        with socket.create_connection(('127.0.0.1',port),timeout=2)as sock:
            session=SharedSession(TcpExchange(sock,a.output),allocation,double_buffer=True)
            result=run(session,profile,a.case,record,observe,begin_cleanup)
    except (Exception,KeyboardInterrupt) as e:
        if not result:
            result=dict(status='failed_before_trial',error=str(e) or type(e).__name__,protocol_cleanup_passed=False,v1_restored=False)
        raise
    finally:
        begin_cleanup()
        result['forward_removed']=False
        if forward_attempted:
            try:
                r=subprocess.run(base+['-O','cancel','-L',forward,destination],capture_output=True,timeout=5)
                result['forward_removed']=r.returncode==0
            except Exception as e:result['forward_error']=str(e)
        try:record(result)
        except Exception as e:
            result.setdefault('recording_errors',[]).append(str(e))
            print('Final recording failed: '+str(e),flush=True)
    print(json.dumps(dict(protocol_cleanup_passed=result.get('protocol_cleanup_passed',False),visual_clearance_required=True,v1_restoration_required=True)))
    return 0 if result.get('protocol_cleanup_passed') and result.get('forward_removed') and result.get('status')=='window_finished' and not result.get('recording_errors') else 2
if __name__=='__main__':raise SystemExit(main())
