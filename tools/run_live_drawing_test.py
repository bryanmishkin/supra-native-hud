#!/usr/bin/env python3
"""Mac launcher for the bounded marker trial through verified head-unit SSH.

Default prints the plan. --execute makes a temporary forward, runs one trial,
and cancels the forward. No SDK, installation, SSH activation or coding edits.
"""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import capture_runtime


def commands(a, port):
    base=capture_runtime.ssh_args(a,'')[:-1]
    destination=base[-1]; options=base[:-1]
    forward='127.0.0.1:%d:160.48.199.96:30502' % port
    if a.socket:
        return (options+['-O','forward','-L',forward,destination],
                options+['-O','cancel','-L',forward,destination])
    return (options+['-o','ExitOnForwardFailure=yes','-N','-L',forward,destination],None)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--head',type=capture_runtime.link_local)
    p.add_argument('--local',type=capture_runtime.link_local)
    p.add_argument('--known-hosts',type=Path)
    p.add_argument('--socket',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps(dict(mode='offline_plan',steps=[
            'Verify existing SSH reaches QNX hu-omap ARM',
            'Temporarily forward localhost to cluster 160.48.199.96:30502',
            'Run one distinct-session marker trial; record all request/reply bytes',
            'Attempt withdrawal, resource removal/check, and session release',
            'Record windshield and factory-function observations; cancel SSH forward'],
            ready='Experimental live candidate; visibility is not established',
            requirements='Parked outdoors, engine idling, windshield HUD visible, cable connected, existing SSH access'),indent=2))
        return 0
    if not all((a.head,a.local,a.known_hosts,a.output)):
        p.error('Requires --head --local --known-hosts --output')
    if not a.known_hosts.is_file():p.error('Verified known-hosts file missing')
    a.output.mkdir(parents=True,exist_ok=False)
    report=dict(forward_started=False,forward_cancelled=False,trial_exit=None)
    proc=None; cancel=None
    def save():
        (a.output/'launcher.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        identity=subprocess.run(capture_runtime.ssh_args(a,'uname -a'),capture_output=True,timeout=10)
        (a.output/'platform.txt').write_bytes(identity.stdout)
        (a.output/'identity-stderr.txt').write_bytes(identity.stderr)
        if identity.returncode or not identity.stdout.startswith(b'QNX hu-omap ') or b'armle' not in identity.stdout:
            raise RuntimeError('Verified ARM QNX hu-omap SSH required; no activation attempted')
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
        start,cancel=commands(a,port)
        with (a.output/'tunnel-stderr.txt').open('wb') as log:
            if cancel:
                report['forward_start_attempted']=True;save()
                r=subprocess.run(start,stdout=log,stderr=log,timeout=10)
                if r.returncode:raise RuntimeError('SSH master refused temporary forwarding')
            else:
                proc=subprocess.Popen(start,stdin=subprocess.DEVNULL,stdout=log,stderr=log)
                # Local listener can race the first client; require it to appear.
                deadline=time.monotonic()+7
                while True:
                    if proc.poll() is not None:raise RuntimeError('SSH tunnel exited before test')
                    with socket.socket() as probe:
                        try:
                            probe.bind(('127.0.0.1',port))
                        except OSError:
                            break
                    if time.monotonic()>=deadline:raise TimeoutError('SSH listener did not start')
                    time.sleep(.05)
            report['forward_started']=True;save()
            command=[sys.executable,str(Path(__file__).with_name('ric_live_trial.py')),
                     '--live','--host','127.0.0.1','--port',str(port),
                     '--output',str(a.output/'trial')]
            # Child has bounded requests/observations and handles SIGINT/SIGTERM.
            child=subprocess.Popen(command)
            while True:
                try:
                    report['trial_exit']=child.wait(timeout=180)
                    break
                except KeyboardInterrupt:
                    # Terminal SIGINT also reaches child; allow its cleanup.
                    continue
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try:report['trial_exit']=child.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        child.kill();child.wait();report['forced_kill_cleanup_unknown']=True
                    raise RuntimeError('Trial exceeded watchdog deadline; inspect cleanup evidence')
    except (Exception,KeyboardInterrupt) as e:
        report['error']=str(e) or type(e).__name__
    finally:
        if cancel and report.get('forward_start_attempted'):
            try:
                r=subprocess.run(cancel,capture_output=True,timeout=10)
                report['forward_cancelled']=r.returncode==0
                report['cancel_error']=r.stderr.decode(errors='replace')
            except Exception as e:report['cancel_error']=str(e)
        if proc:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            report['forward_cancelled']=True
        save()
    print(json.dumps(report,indent=2))
    return 0 if report['trial_exit']==0 and report['forward_cancelled'] else 2


if __name__=='__main__':sys.exit(main())
