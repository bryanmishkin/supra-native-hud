#!/usr/bin/env python3
"""Read-only PiP phase metadata capture; default prints an offline plan.
No drawing, restart, hooks, shared-memory writes, or installed-file changes.
Run alongside the existing verified passive packet recorder.
"""
import argparse, hashlib, json, subprocess, time
from pathlib import Path
import capture_runtime as runtime
PHASES=('normal','radio-open','radio-closed','navigation-start','navigation-visible','navigation-stop','normal-final')
COMMANDS=(('processes','pidin ar'),('sockets','netstat -an'),
          ('shared-memory','ls -l /dev/shmem'),('screen-inventory','ls -l /dev/screen'))
LIMIT=4*1024*1024

def plan():
    return {'phases':list(PHASES),'commands':dict(COMMANDS),
            'remote_writes':False,'per_command_timeout_seconds':20,
            'packet_recorder':'Run consolidated_capture.py --record-only separately; wait for recording_ready before actions.',
            'limits':'Metadata snapshots only. Screen inventory may be unavailable. No automatic pixel-source or routing conclusion.'}

def collect(a):
    folder=a.output/a.phase
    folder.mkdir(parents=True,exist_ok=False)
    report={'phase':a.phase,'start_epoch':time.time(),'rows':[],
            'pixel_source_proven':False,'windshield_routing_proven':False}
    def persist():
        (folder/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    def run(name,command):
        row={'name':name,'command':command,'start_epoch':time.time()}
        try:
            p=subprocess.run(runtime.ssh_args(a,command),capture_output=True,timeout=20)
            row.update(exit_code=p.returncode,bytes=len(p.stdout),stderr=p.stderr.decode(errors='replace')[:2000])
            if len(p.stdout)>LIMIT:
                row['status']='oversized';return None
            (folder/(name+'.txt')).write_bytes(p.stdout)
            row.update(status='captured' if p.returncode==0 else 'unavailable',sha256=hashlib.sha256(p.stdout).hexdigest())
            return p.stdout if p.returncode==0 else None
        except (OSError,subprocess.TimeoutExpired) as e:
            row.update(status='failed',error=str(e));return None
        finally:
            row['end_epoch']=time.time();report['rows'].append(row);persist()
    identity=run('identity','uname -a')
    if not identity or not identity.startswith(b'QNX hu-omap ') or b'armle' not in identity:
        raise ValueError('Direct ARM QNX hu-omap identity not verified')
    for name,command in COMMANDS:run(name,command)
    report['end_epoch']=time.time()
    report['phase_metadata_complete']=all(r['status']=='captured' for r in report['rows'])
    persist()
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--phase',choices=PHASES)
    p.add_argument('--head',type=runtime.link_local);p.add_argument('--local',type=runtime.link_local)
    p.add_argument('--known-hosts',type=Path);p.add_argument('--socket',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:print(json.dumps(plan(),indent=2));return 0
    if not all((a.phase,a.head,a.local,a.known_hosts,a.output)):p.error('Execution requires phase, verified addresses, known-hosts and output')
    try:
        result=collect(a);print(json.dumps(result,indent=2));return 0 if result['phase_metadata_complete'] else 2
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
