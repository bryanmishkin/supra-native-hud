#!/usr/bin/env python3
"""Read-only capture of the missing PiP compositor; offline plan by default.
Reuses bounded, double-read, hash-verified transfers. Never sets layer properties.
"""
import argparse,json,re
from pathlib import Path
from elftools.elf.elffile import ELFFile
import capture_runtime as runtime
from consolidated_capture import Session,DIRS
FILES=('/opt/sys/bin/LayerManagerService','/opt/sys/bin/LayerManagerControl')
COMMANDS=(('processes','pidin ar'),('loader','getconf CS_LIBPATH'),
          ('pip-surface','/opt/sys/bin/LayerManagerControl get surface 1056'))

def needed(path):
    with path.open('rb') as f:
        e=ELFFile(f)
        if e.elfclass!=32 or not e.little_endian or e['e_machine']!='EM_ARM':
            raise ValueError('Expected reference ARM little-endian ELF')
        names=[t.needed for s in e.iter_segments() if s['p_type']=='PT_DYNAMIC'
               for t in s.iter_tags() if t.entry.d_tag=='DT_NEEDED']
    if any(not re.fullmatch(r'[A-Za-z0-9_.+-]+',n) for n in names):
        raise ValueError('Unsafe dependency name')
    return names

def plan():
    return dict(files=list(FILES),commands=dict(COMMANDS),dependency_directories=list(DIRS),
        dependency_closure=True,process_maps=True,remote_writes=False,
        driving_required=False,restart_required=False,drawing_test=False,
        limits='Existing Session limits: 64 MiB/file, 512 MiB/session, 1200 seconds; double-read files.',
        limitation='LayerManagerControl path is supported by reference source, not verified present on this unit. Missing files, dependencies, maps or surface output are incomplete evidence. No drawing authorization.')

def collect(a):
    s=Session(a);s.identity();paths=[];missing=[];maps=[];mapped=set()
    for name,cmd in COMMANDS:
        r=s.call(cmd);(s.root/(name+'.txt')).write_bytes(r.stdout)
        if r.returncode:missing.append(name)
    for line in (s.root/'processes.txt').read_text(errors='replace').splitlines():
        cols=line.split()
        if len(cols)>1 and cols[0].isdigit() and Path(cols[1]).name=='LayerManagerService':
            maps.append(cols[0]);r=s.call('pidin -p '+cols[0]+' mem')
            (s.root/('maps-'+cols[0]+'.txt')).write_bytes(r.stdout)
            if r.returncode:missing.append('map-'+cols[0])
            mapped.update(re.findall(r'\b[A-Za-z0-9_+.-]+\.so(?:\.[A-Za-z0-9_+.-]+)?',r.stdout.decode(errors='replace')))
    if not maps:missing.append('LayerManagerService process')
    for name in FILES:
        p=s.file(name)
        if p:needed(p);paths.append(p)
        else:missing.append(name)
    seen=set()
    def fetch(name):
        if name in seen:return
        seen.add(name)
        if len(seen)>128:raise ValueError('Dependency count limit')
        for directory in DIRS:
            p=s.file(directory+'/'+name)
            if p:needed(p);paths.append(p);return
        missing.append('dependency:'+name)
    for name in sorted(mapped):fetch(name)
    for p in paths:
        for name in needed(p):fetch(name)
    s.report.update(missing=missing,capture_complete=not missing,
                    pixel_transport_proven=False,drawing_test_ready=False)
    s.persist();return s.report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--head',type=runtime.link_local);p.add_argument('--local',type=runtime.link_local)
    p.add_argument('--known-hosts',type=Path);p.add_argument('--socket',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:print(json.dumps(plan(),indent=2));return 0
    if not all((a.head,a.local,a.known_hosts,a.output)):p.error('Execution requires verified addresses, known hosts and output')
    try:
        r=collect(a);print(json.dumps(r,indent=2));return 0 if r['capture_complete'] else 2
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
