#!/usr/bin/env python3
"""Read-only capture of the missing PiP compositor; offline plan by default.
Reuses bounded, double-read, hash-verified transfers. Never sets layer properties.
"""
import argparse,json,re
from pathlib import Path
from elftools.elf.elffile import ELFFile
import capture_runtime as runtime
from consolidated_capture import Session,DIRS
FILES=('/opt/sys/bin/LayerManagerService','/opt/sys/bin/LayerManagerControl',
       '/lib/graphics/omap5430/libWFDomap5430ES2_0.so',
       '/lib/graphics/omap5430/libwfdcfg-emodule-hu.so',
       '/lib/graphics/omap5430/libwfdcfg.so.0')
CONFIG_FILES=('/lib/graphics/omap5430/graphics.conf',
              '/lib/graphics/omap5430/graphics-1280_480.conf')
MAP_PROCESSES=('LayerManagerService','screen')
CONTROL='LD_LIBRARY_PATH=/opt/sys/lib:/lib:/boot/lib /opt/sys/bin/LayerManagerControl '
COMMANDS=(('processes','pidin ar'),('loader','getconf CS_LIBPATH'),
          ('pip-surface',CONTROL+'get surface 1056'),
          ('screen-0',CONTROL+'get screen 0'),('screen-1',CONTROL+'get screen 1'))

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
    return dict(files=list(FILES),config_files=list(CONFIG_FILES),map_processes=list(MAP_PROCESSES),commands=dict(COMMANDS),dependency_directories=list(DIRS),
        dependency_closure=True,process_maps=True,remote_writes=False,
        driving_required=False,restart_required=False,drawing_test=False,
        limits='Existing Session limits: 64 MiB/file, 512 MiB/session, 1200 seconds; double-read files.',
        limitation='Paths are grounded in the saved 18 November inventory. Output-driver contents remain uncaptured. Missing files, dependencies, maps or surface output are incomplete evidence. No drawing authorization.')

def collect(a):
    s=Session(a);s.identity();paths=[];missing=[];maps=[];mapped=set();found_processes=set()
    for name,cmd in COMMANDS:
        r=s.call(cmd);(s.root/(name+'.txt')).write_bytes(r.stdout)
        if r.returncode:missing.append(name)
    for line in (s.root/'processes.txt').read_text(errors='replace').splitlines():
        cols=line.split()
        if len(cols)>1 and cols[0].isdigit() and Path(cols[1]).name in MAP_PROCESSES:
            found_processes.add(Path(cols[1]).name)
            maps.append(cols[0]);r=s.call('pidin -p '+cols[0]+' mem')
            (s.root/('maps-'+cols[0]+'.txt')).write_bytes(r.stdout)
            if r.returncode:missing.append('map-'+cols[0])
            mapped.update(re.findall(r'\b[A-Za-z0-9_+.-]+\.so(?:\.[A-Za-z0-9_+.-]+)?',r.stdout.decode(errors='replace')))
    for process in MAP_PROCESSES:
        if process not in found_processes:missing.append(process+' process')
    for name in CONFIG_FILES:
        if not s.file(name):missing.append(name)
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
    # pidin truncates long basenames from the left. Resolve only unique suffixes
    # against files actually verified through the ELF dependency closure.
    verified={Path(k).name for k,v in s.report['files'].items()
              if v['status'] in ('verified','reverified')}
    aliases={}
    for item in list(missing):
        if item.startswith('dependency:'):
            suffix=item.split(':',1)[1]
            matches=[n for n in verified if n.endswith(suffix)]
            if suffix in mapped and len(matches)==1:
                aliases[suffix]=matches[0];missing.remove(item)
    s.report.update(mapped_suffix_resolutions=aliases,missing=missing,capture_complete=not missing,
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
