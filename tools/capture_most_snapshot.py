#!/usr/bin/env python3
"""Bounded MOST registry/header snapshot. Plan by default; never installs V1."""
import argparse,hashlib,json,re,uuid
from pathlib import Path
import capture_runtime as runtime
from consolidated_capture import Session,save
from capture_output_driver import snapshot,BASELINE

def assess(raw):
    rows=[]
    for line in raw.decode().splitlines():
        if line.startswith('{'):
            try:rows.append(json.loads(line))
            except ValueError:pass
    if len(rows)!=1:raise ValueError('Expected exactly one observer result')
    d=rows[0]
    if d.get('schema')!=2 or d.get('all_headers') is not True:raise ValueError('Wrong observer schema/mode')
    if d.get('hud_commands_sent')!=0 or d.get('payloads_captured') is not False:raise ValueError('Observer scope mismatch')
    if d.get('link_state')!='up' or not d.get('snapshots'):raise ValueError('No healthy registry snapshot')
    if any(d.get(k)!=0 for k in ('dropped_snapshots','dropped_headers','bad_messages')):raise ValueError('Incomplete/corrupt observer data')
    if not 14000<=d.get('elapsed_ms',0)<=20000:raise ValueError('Unexpected observation interval')
    return d

def run(a):
    raw=a.binary.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.sha256 or raw[:6]!=b'\x7fELF\x01\x01' or raw[18:20]!=b'\x28\x00':raise ValueError('Observer identity mismatch')
    if a.output.exists():raise ValueError('Use a new evidence directory')
    s=Session(a);s.identity();expected=json.loads(BASELINE.read_text())['component_sha256']
    before=snapshot(s,'v1-before',expected)
    if not before['all_15_match']:raise ValueError('V1 mismatch; no observer started')
    remote='/fs/ram5/most-observe-'+uuid.uuid4().hex[:12];made=False
    report={'complete':False,'remote_directory':remote,'binary_sha256':a.sha256,
            'bus_wide_capture':False,'server_registration_cleanup_proven':False}
    try:
        if s.call('umask 077; mkdir '+remote).returncode:raise ValueError('RAM directory unavailable')
        made=True
        if s.call('cat > '+remote+'/observer',input=raw).returncode:raise ValueError('Upload failed')
        if s.call('cat '+remote+'/observer').stdout!=raw:raise ValueError('Readback mismatch')
        if s.call('chmod 700 '+remote+'/observer').returncode:raise ValueError('chmod failed')
        r=s.call('LD_LIBRARY_PATH=/opt/sys/lib:/boot/lib:/lib '+remote+'/observer --observe-registry --all-headers',timeout=30)
        (s.root/'observer.stdout').write_bytes(r.stdout);(s.root/'observer.stderr').write_bytes(r.stderr)
        report['exit']=r.returncode
        if r.returncode:raise ValueError('Observer did not exit successfully')
        report['observation']=assess(r.stdout)
    except Exception as e:report['error']=str(e)
    finally:
        if made:
            try:
                r=s.call('pidin ar',cleanup=True);(s.root/'processes-after.txt').write_bytes(r.stdout)
                report['process_absent']=r.returncode==0 and (remote+'/observer').encode() not in r.stdout
                if report['process_absent']:
                    r=s.call('rm -f '+remote+'/observer && rm -r '+remote+' && test ! -e '+remote,cleanup=True)
                    report['ram_removed']=r.returncode==0
            except Exception as e:report['cleanup_error']=str(e)
        try:
            after=snapshot(s,'v1-after',expected)
            report['v1_matches']=after['all_15_match'];report['faults_unchanged']=before['faults']==after['faults']
        except Exception as e:report['verification_error']=str(e)
        report['complete']=all(report.get(k) for k in ('observation','process_absent','ram_removed','v1_matches','faults_unchanged')) and 'error' not in report
        save(s.root/'most-result.json',report);s.persist()
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    for n in ('head','local'):p.add_argument('--'+n,type=runtime.link_local)
    for n in ('known-hosts','socket','output','binary'):p.add_argument('--'+n,type=Path)
    p.add_argument('--sha256');a=p.parse_args()
    if not a.execute:
        print(json.dumps({'seconds':15,'deadline_seconds':20,'target_requests':False,'writes':'unique RAM directory only','capture':'registry and headers delivered to temporary client; not full bus','v1':'15 hashes and faults before/after','cleanup_limit':'process/file cleanup checked; server-side registration release not independently proven'},indent=2));return 0
    if not all((a.head,a.local,a.known_hosts,a.output,a.binary,a.sha256)) or not re.fullmatch('[a-f0-9]{64}',a.sha256):p.error('Verified SSH inputs, fresh output, binary and SHA256 required')
    r=run(a);print(json.dumps(r,indent=2));return 0 if r['complete'] else 2
if __name__=='__main__':raise SystemExit(main())
