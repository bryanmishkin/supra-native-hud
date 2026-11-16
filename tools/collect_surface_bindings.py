#!/usr/bin/env python3
"""Read-only targeted binding capture. Default is a local plan, with no SSH.
Paths come from captured process arguments. Never changes configuration or starts services.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
import capture_runtime as runtime
FILES=('/opt/nav/eceusa/bin/navigation.ini','/mnt/share/nav/NavCtrl_DB.ini','/etc/someip/someip.conf')
LIMIT=1024*1024

def plan():
    return dict(remote_files=list(FILES),max_file_bytes=LIMIT,double_read=True,remote_writes=False,
                purpose='Identify active DNAVIManeuverView provider and SOME/IP routing configuration; contents are private evidence.')

def collect(a):
    a.output.mkdir(parents=True,exist_ok=False);log=[];manifest=[]
    def read(command):
        try:
            r=subprocess.run(runtime.ssh_args(a,command),capture_output=True,timeout=30)
            log.append(dict(command=command,exit_code=r.returncode,bytes=len(r.stdout),stderr=r.stderr.decode(errors='replace')[:1000]))
            return r.returncode,r.stdout
        except subprocess.TimeoutExpired:
            log.append(dict(command=command,error='timeout'));return -1,b''
        finally:(a.output/'commands.json').write_text(json.dumps(log,indent=2)+'\n')
    code,data=read('uname -a');(a.output/'platform.txt').write_bytes(data)
    if code or not data.startswith(b'QNX hu-omap ') or b'armle' not in data:raise ValueError('Direct ARM QNX hu-omap identity not verified')
    for i,path in enumerate(FILES):
        cmd='dd if='+path+' bs=4096 count=257'
        code,data=read(cmd)
        row=dict(remote_path=path)
        if code:row['status']='read_failed'
        elif len(data)>LIMIT:row['status']='too_large'
        else:
            code,again=read(cmd)
            if code or again!=data:row['status']='unstable_or_failed_repeat'
            else:
                name='%02d-%s'%(i,Path(path).name);(a.output/name).write_bytes(data)
                row.update(status='captured',file=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),double_read_match=True)
        manifest.append(row);(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return all(x['status']=='captured' for x in manifest)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--head',type=runtime.link_local);p.add_argument('--local',type=runtime.link_local);p.add_argument('--known-hosts',type=Path);p.add_argument('--socket',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:print(json.dumps(plan(),indent=2));return 0
    if not all((a.head,a.local,a.known_hosts,a.output)):p.error('--execute requires --head, --local, --known-hosts and --output')
    try:return 0 if collect(a) else 2
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
