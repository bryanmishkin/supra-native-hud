#!/usr/bin/env python3
"""Host-side kit runner. Dry-run by default; explicit --execute enables SSH.
No passwords, SSH activation, host-key bypass, routes or persistent installation.
"""
import argparse,hashlib,json,re,subprocess,time,uuid
from pathlib import Path
from extract_someip_pcap import extract

PREFLIGHT='uname -a; ifconfig -a; netstat -rn; ls -ld /tmp /fs/ram5; ls -l /dev/bpf* 2>/dev/null; command -v tcpdump; command -v ipgrabber; mount'

def validate(host,interface,label):
    if not re.fullmatch(r'(?:[A-Za-z0-9_]+@)?[0-9]+(?:\.[0-9]+){3}',host):raise ValueError('Use the verified head-unit IPv4 address, optionally user@address')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,31}',interface):raise ValueError('Invalid interface')
    if label not in ('baseline','radio','navigation'):raise ValueError('Invalid capture label')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',required=True);p.add_argument('--interface',default='vlan73')
    p.add_argument('--label',choices=['baseline','radio','navigation'],default='baseline')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true')
    p.add_argument('--preflight-only',action='store_true')
    p.add_argument('--binary',type=Path,default=Path(__file__).with_name('supra-passive-capture-qnx'))
    p.add_argument('--manifest',type=Path,default=Path(__file__).with_name('capture-manifest.json'))
    a=p.parse_args()
    try:validate(a.host,a.interface,a.label)
    except ValueError as e:p.error(str(e))
    if not a.execute:
        print(json.dumps(dict(dry_run=True,host=a.host,interface=a.interface,label=a.label,preflight_only=a.preflight_only,limits='15 seconds / 8 MiB / 4096 packets; 20-second hard deadline',note='Confirm interface and internal address from preflight. No SSH command executed.'),indent=2));return 0
    a.output.mkdir(parents=True,exist_ok=False)
    ssh=['ssh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=5',a.host]
    def call(command,timeout=30,input=None):return subprocess.run(ssh+[command],input=input,capture_output=True,timeout=timeout)
    report={'label':a.label,'host':a.host,'interface':a.interface,'started_epoch':time.time(),'capture_valid':False}
    remote='/fs/ram5/supra-capture-'+uuid.uuid4().hex
    created=False
    try:
        pre=call(PREFLIGHT);(a.output/'preflight.txt').write_bytes(pre.stdout+pre.stderr)
        report['preflight_exit_code']=pre.returncode
        if pre.returncode:raise ValueError('Preflight SSH/command failed; review saved output')
        if a.preflight_only:
            report['preflight_completed']=True
            return 0
        interface=call('ifconfig '+a.interface)
        (a.output/'interface.txt').write_bytes(interface.stdout+interface.stderr)
        text=interface.stdout.decode(errors='replace')
        if interface.returncode or not re.search(r'\binet\s+160\.48\.199\.119\b',text) or not re.search(r'<[^>]*\bUP\b',text):raise ValueError('Selected interface lacks expected active internal IPv4; review preflight')
        raw=a.binary.read_bytes();manifest=json.loads(a.manifest.read_text())
        if hashlib.sha256(raw).hexdigest()!=manifest['sha256'] or not manifest['static_gate_passed']:raise ValueError('Candidate hash/static gate mismatch')
        made=call('umask 077; mkdir '+remote)
        if made.returncode:raise ValueError('Cannot create isolated RAM directory')
        created=True;target=remote+'/capture'
        uploaded=call('cat > '+target,input=raw)
        if uploaded.returncode:raise ValueError('Upload failed')
        readback=call('cat '+target)
        if readback.returncode or readback.stdout!=raw:raise ValueError('Uploaded candidate differs')
        if call('chmod 700 '+target).returncode:raise ValueError('Cannot set candidate executable')
        result=call(target+' --capture '+a.interface,timeout=28)
        (a.output/(a.label+'.pcap')).write_bytes(result.stdout)
        (a.output/'capture-stderr.txt').write_bytes(result.stderr)
        report['exit_code']=result.returncode
        report['pcap_sha256']=hashlib.sha256(result.stdout).hexdigest()
        lines=[line for line in result.stderr.decode(errors='replace').splitlines() if line.startswith('{')]
        summary=json.loads(lines[-1]) if lines else {};report['capture_summary']=summary
        # Strict parser rejection preserves raw evidence and prevents a false pass.
        parsed=extract(result.stdout)
        for stream in parsed['streams']:stream.pop('data')
        (a.output/'inventory.json').write_text(json.dumps(parsed,indent=2)+'\n')
        report['capture_valid']=(result.returncode==0 and summary.get('reason')=='duration' and summary.get('elapsed_s',0)>=14.5 and summary.get('packets',0)>0 and summary.get('drops')==0 and summary.get('interface_drops')==0 and summary.get('pcap_bytes')==len(result.stdout))
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:
        report['error']=str(e)
    finally:
        if created:
            try:
                clean=call('rm -f '+remote+'/capture && rm -r '+remote+' && test ! -e '+remote)
                report['cleanup_verified']=clean.returncode==0
                (a.output/'cleanup.txt').write_bytes(clean.stdout+clean.stderr)
            except (OSError,subprocess.TimeoutExpired) as e:report['cleanup_verified']=False;report['cleanup_error']=str(e)
        (a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['capture_valid'] and report.get('cleanup_verified') else 2
if __name__=='__main__':raise SystemExit(main())
