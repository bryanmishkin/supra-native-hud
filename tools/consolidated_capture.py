#!/usr/bin/env python3
"""Private, resumable evidence collection. Offline plan unless --execute is explicit.
Never activates SSH, restarts software, changes coding or requests a HUD object.
"""
import argparse,hashlib,json,re,subprocess,time,uuid,shutil,shlex
from pathlib import Path
from types import SimpleNamespace
from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError
import capture_runtime as runtime
from extract_someip_pcap import extract
from capture_evidence import assess
FILES=(
 '/opt/nav/eceusa/bin/NavNBTEvoController','/opt/nav/eceusa/bin/NavigationBasic',
 '/opt/nav/eceusa/bin/NavigationFully','/opt/nav/eceusa/bin/NavigationOnOff',
 '/opt/sys/bin/someip_sddaemon','/opt/sys/bin/someip_enhtestability_server',
 '/opt/nav/eceusa/bin/navigation.ini','/mnt/share/nav/NavCtrl_DB.ini',
 '/etc/someip/services.conf','/etc/someip/someip.conf',
 '/opt/nav/eceusa/bin/Appstarter.ini','/opt/nav/eceusa/bin/NavigationEceUsa.cfg',
 '/opt/nav/eceusa/bin/Navigation.hbtc','/etc/dsi/services.conf')
DIRS=('/boot/lib','/lib','/opt/sys/lib','/opt/hmi/ID5/lib','/opt/car/lib','/usr/lib','/lib/graphics/omap5430')
MAX_FILE=64*1024*1024
MAX_TOTAL=512*1024*1024

def digest(b):return hashlib.sha256(b).hexdigest()
def save(path,value):
    tmp=path.with_suffix(path.suffix+'.partial');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def plan():
    return dict(files=list(FILES),dependency_directories=list(DIRS),dynamic_dependencies=True,
        limits=dict(per_file_bytes=MAX_FILE,total_transfer_bytes=MAX_TOTAL,session_seconds=1200,capture_seconds=120,capture_bytes=MAX_FILE,capture_packets=65536),
        resume='Local SHA verified; fresh remote read must match before reuse, otherwise double-read anew.',
        startup='Recorder begins only after SSH and READY. Cold-boot allocation is NOT guaranteed. No restart or persistent hook.',
        conclusions='File completeness and lifecycle evidence are separate gates; successful capture never grants drawing ownership.')

class Session:
    def __init__(self,a,transport=None):
        self.a=a;self.root=a.output;self.root.mkdir(parents=True,exist_ok=True)
        self.transport=transport;self.start=time.monotonic();self.total=0
        self.report={'schema':1,'files':{},'commands':[],'provider_binding_proven':False,'independent_surface_proven':False}
        if (self.root/'manifest.json').exists():
            old=json.loads((self.root/'manifest.json').read_text());self.report['files']=old.get('files',{})
        self.persist()
    def persist(self):
        self.report['transferred_bytes']=self.total;save(self.root/'manifest.json',self.report)
    def call(self,cmd,timeout=45,input=None,cleanup=False):
        if not cleanup and (time.monotonic()-self.start>1200 or self.total>=MAX_TOTAL):raise ValueError('Session budget exhausted')
        r=self.transport(cmd,timeout,input) if self.transport else subprocess.run(runtime.ssh_args(self.a,cmd),input=input,capture_output=True,timeout=timeout)
        self.total+=len(r.stdout)
        self.report['commands'].append(dict(command=cmd,exit=r.returncode,bytes=len(r.stdout),stderr=r.stderr.decode(errors='replace')[:2000]))
        self.persist()
        if not cleanup and self.total>MAX_TOTAL:raise ValueError('Transfer budget exceeded')
        return r
    def identity(self):
        r=self.call('uname -a')
        (self.root/'platform.txt').write_bytes(r.stdout)
        if r.returncode or not r.stdout.startswith(b'QNX hu-omap ') or b'armle' not in r.stdout:raise ValueError('Direct ARM QNX hu-omap not verified')
        self.report['identity_verified']=True;self.persist()
    def file(self,path):
        if not re.fullmatch(r'/[A-Za-z0-9_./+-]+',path) or '..' in path.split('/'):raise ValueError('Unsafe path')
        # Filename is derived locally, never trusted from an old manifest.
        name='files/'+hashlib.sha256(path.encode()).hexdigest()[:16]+'-'+Path(path).name
        target=self.root/name;target.parent.mkdir(exist_ok=True)
        old=self.report['files'].get(path,{})
        row={'file':name,'status':'pending'};self.report['files'][path]=row;self.persist()
        cmd='dd if='+path+' bs=4096 count=16385'
        try:
            r=self.call(cmd)
            if r.returncode:row.update(status='unavailable',error=r.stderr.decode(errors='replace')[:1000]);return None
            if len(r.stdout)>MAX_FILE:row['status']='oversized';return None
            b=r.stdout;sha=digest(b)
            cached=old.get('status') in ('verified','reverified') and old.get('sha256')==sha and target.is_file() and digest(target.read_bytes())==sha
            if cached:row.update(status='reverified',sha256=sha,bytes=len(b),fresh_remote_match=True);return target
            again=self.call(cmd)
            if again.returncode or again.stdout!=b:row['status']='unstable';return None
            tmp=target.with_suffix(target.suffix+'.partial');tmp.write_bytes(b);tmp.replace(target)
            row.update(status='verified',sha256=sha,bytes=len(b),double_read_match=True);return target
        except (OSError,subprocess.TimeoutExpired) as e:row.update(status='error',error=str(e));return None
        finally:self.persist()
    def collect(self):
        self.identity()
        paths=[]
        for path in FILES:
            p=self.file(path)
            if p:
                if path in FILES[:6] and p.read_bytes()[:4]!=b'\x7fELF':self.report['files'][path]['status']='invalid_elf';self.persist()
                else:paths.append(p)
        self.report['metadata_complete']=True
        # Fixed commands only; pid selection comes from exact process-name matches.
        for name,cmd in [('processes','pidin ar'),('sockets','netstat -an'),('interfaces','ifconfig -a'),('loader','getconf CS_LIBPATH'),('library-list','ls -l '+' '.join(DIRS))]:
            r=self.call(cmd);(self.root/(name+'.txt')).write_bytes(r.stdout)
            if r.returncode:self.report['metadata_complete']=False
        processes=(self.root/'processes.txt').read_text(errors='replace')
        mapped_names=set();extra_configs=set()
        for line in processes.splitlines():
            parts=line.split()
            if len(parts)>1 and parts[0].isdigit() and Path(parts[1]).name in ('NavNBTEvoController','NavigationBasic','NavigationFully','NavigationOnOff'):
                pid=parts[0];r=self.call('pidin -p '+pid+' mem');(self.root/('maps-'+pid+'.txt')).write_bytes(r.stdout)
                if r.returncode:self.report['metadata_complete']=False
                mapped_names.update(re.findall(r'\b[A-Za-z0-9_+.-]+\.so(?:\.[A-Za-z0-9_+.-]+)?',r.stdout.decode(errors='replace')))
                for arg in shlex.split(line):
                    if arg.startswith(('--config=','--config+=','--tp=')):
                        value=arg.split('=',1)[1]
                        if not value.startswith('/'):value='/opt/nav/eceusa/bin/'+value
                        if value.startswith(('/opt/nav/','/mnt/share/nav/','/var/opt/nav/')) and value.endswith(('.ini','.cfg','.hbtc')):extra_configs.add(value)
        for path in sorted(extra_configs-set(FILES)):
            p=self.file(path)
            if p:paths.append(p)
        # Read-only DT_NEEDED closure; each new basename searched once in fixed dirs.
        seen=set();missing=[];missing_mapped=[]
        # Mapped names can be truncated by pidin; unresolved candidates remain explicit.
        for name in sorted(mapped_names):
            for directory in DIRS:
                found=self.file(directory+'/'+name)
                if found:paths.append(found);seen.add(name);break
            else:missing_mapped.append(name)
        for p in paths:
            if p.read_bytes()[:4]!=b'\x7fELF':continue
            with p.open('rb') as f:
                elf=ELFFile(f)
                if elf.elfclass!=32 or not elf.little_endian or elf['e_machine']!='EM_ARM':raise ValueError('Unexpected captured ELF architecture: '+str(p))
                names=[t.needed for seg in elf.iter_segments() if seg['p_type']=='PT_DYNAMIC' for t in seg.iter_tags() if t.entry.d_tag=='DT_NEEDED']
            for name in names:
                if name in seen:continue
                seen.add(name)
                if len(seen)>128:raise ValueError('Dependency count limit')
                if not re.fullmatch(r'[A-Za-z0-9_.+-]+',name):raise ValueError('Unsafe dependency name')
                for directory in DIRS:
                    found=self.file(directory+'/'+name)
                    if found:paths.append(found);break
                else:missing.append(name)
        self.report['missing_dependencies']=missing
        self.report['unresolved_mapped_candidates']=missing_mapped
        self.report['files_complete']=all(self.report['files'].get(p,{}).get('status') in ('verified','reverified') for p in FILES if p!='/mnt/share/nav/NavCtrl_DB.ini') and not missing
        self.report['unavailable_extra_configs']=[p for p in sorted(extra_configs-set(FILES)) if self.report['files'].get(p,{}).get('status') not in ('verified','reverified')]
        self.report['local_hashes_verified']=all((self.root/r['file']).is_file() and digest((self.root/r['file']).read_bytes())==r['sha256'] for r in self.report['files'].values() if r['status'] in ('verified','reverified'))
        self.report['files_complete']=self.report['files_complete'] and self.report['local_hashes_verified'] and not self.report['unavailable_extra_configs']
        self.report['bundle_complete']=self.report['files_complete'] and self.report['metadata_complete']
        self.report['startup_covered']=False
        self.report['optional_override_status']=self.report['files'].get('/mnt/share/nav/NavCtrl_DB.ini',{}).get('status')
        self.persist()

    def record(self,binary,expected_hash):
        raw=binary.read_bytes()
        if digest(raw)!=expected_hash or raw[:6]!=b'\x7fELF\x01\x01' or raw[18:20]!=b'\x28\x00':raise ValueError('Recorder hash or ARM ELF identity mismatch')
        r=self.call('ifconfig vlan73')
        if r.returncode or not re.search(rb'<[^>]*\bUP\b',r.stdout) or not re.search(rb'\binet\s+160\.48\.199\.119\b',r.stdout):raise ValueError('Internal vlan73 identity not verified')
        remote='/fs/ram5/shud-'+uuid.uuid4().hex[:12];made=False
        folder=self.root/('recording-'+uuid.uuid4().hex[:8]);folder.mkdir()
        result={'capture_valid':False,'creation_exchange_observed':False,'startup_covered':False,'remote_directory':remote}
        try:
            if self.call('umask 077; mkdir '+remote).returncode:raise ValueError('RAM directory unavailable')
            made=True
            if self.call('cat > '+remote+'/capture',input=raw).returncode:raise ValueError('Upload failed')
            if self.call('cat '+remote+'/capture').stdout!=raw:raise ValueError('Upload readback differs')
            if self.call('chmod 700 '+remote+'/capture').returncode:raise ValueError('chmod failed')
            before=time.time();clock=self.call('date +%s');after=time.time()
            result['clock_sample']={'host_before':before,'host_after':after,'remote_epoch_text':clock.stdout.decode(errors='replace').strip(),'resolution_seconds':1,'exit':clock.returncode,'valid_numeric_epoch':clock.returncode==0 and clock.stdout.strip().isdigit()}
            started=time.time();started_mono=time.monotonic();result['host_start_epoch']=started
            # Stream evidence to disk. READY is emitted by the remote recorder only after opening BPF.
            with (folder/'traffic.pcap').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
                proc=subprocess.Popen(runtime.ssh_args(self.a,remote+'/capture --capture vlan73'),stdout=out,stderr=err)
                ready=False
                try:
                    while proc.poll() is None:
                        if time.monotonic()-started_mono>140:raise subprocess.TimeoutExpired('continuous capture',140)
                        if (folder/'traffic.pcap').stat().st_size>MAX_FILE:raise ValueError('Capture size limit')
                        if not ready and b'"ready":true' in (folder/'stderr.txt').read_bytes():
                            ready=True;result['ready_seen_epoch']=time.time();save(folder/'status.json',result)
                            print(json.dumps({'recording_ready':True,'folder':str(folder),'seconds':120}),flush=True)
                        time.sleep(.2)
                finally:
                    if proc.poll() is None:
                        proc.terminate()
                        try:proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
            result['exit_code']=proc.returncode
            lines=[json.loads(x) for x in (folder/'stderr.txt').read_text().splitlines() if x.startswith('{')]
            stats=next((x for x in reversed(lines) if 'packets' in x),{})
            result['stats']=stats
            data=(folder/'traffic.pcap').read_bytes();result['sha256']=digest(data)
            parsed=extract(data,max_bytes=MAX_FILE,max_packets=65536)
            lifecycle=assess(parsed);save(folder/'lifecycle.json',lifecycle)
            result['creation_exchange_observed']=lifecycle['matched_guidance_create']>0
            result['capture_valid']=any(x.get('ready') is True for x in lines) and proc.returncode==0 and stats.get('reason')=='duration' and stats.get('elapsed_s',0)>=119.5 and stats.get('packets',0)>0 and stats.get('drops')==0 and stats.get('interface_drops')==0 and stats.get('pcap_bytes')==len(data) and all(not s['parse_error'] for s in parsed['streams'])
            for i,s in enumerate(parsed['streams']):
                fn='stream-%03d.bin'%i;(folder/fn).write_bytes(s.pop('data'));s['file']=fn
            save(folder/'inventory.json',parsed)
        except (OSError,ValueError,ELFError,subprocess.TimeoutExpired) as e:result['error']=str(e)
        finally:
            if made:
                try:
                    state=self.call('pidin ar',cleanup=True)
                    (folder/'post-processes.txt').write_bytes(state.stdout)
                    result['capture_process_absent']=state.returncode==0 and (remote+'/capture').encode() not in state.stdout
                    clean=self.call('rm -f '+remote+'/capture && rm -r '+remote+' && test ! -e '+remote,cleanup=True)
                    result['cleanup_verified']=clean.returncode==0 and result['capture_process_absent']
                except (OSError,ValueError,ELFError,subprocess.TimeoutExpired) as e:result['cleanup_verified']=False;result['cleanup_error']=str(e)
            save(folder/'result.json',result)
        self.report['latest_recording']=str(folder);self.report['capture_valid']=result['capture_valid'];self.report['creation_exchange_observed']=result['creation_exchange_observed'];self.persist()
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--head',type=runtime.link_local);p.add_argument('--local',type=runtime.link_local);p.add_argument('--known-hosts',type=Path);p.add_argument('--socket',type=Path);p.add_argument('--output',type=Path);p.add_argument('--record',action='store_true');p.add_argument('--record-only',action='store_true');p.add_argument('--binary',type=Path);p.add_argument('--sha256')
    a=p.parse_args()
    if not a.execute:print(json.dumps(plan(),indent=2));return 0
    if not all((a.head,a.local,a.known_hosts,a.output)):p.error('Execution requires verified addresses, known-hosts and output')
    if a.record or a.record_only:
        if not a.binary or not a.sha256 or not re.fullmatch('[a-f0-9]{64}',a.sha256):p.error('Recording requires exact candidate binary and SHA256')
    a.output.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(a.output).free<1024*1024*1024:p.error('At least 1 GiB free local space required')
    session=Session(a)
    try:
        if a.record_only:session.identity()
        else:session.collect()
        if a.record or a.record_only:
            r=session.record(a.binary,a.sha256)
            if not r['capture_valid'] or not r.get('cleanup_verified'):return 2
        print(json.dumps(session.report,indent=2));return 0 if session.report.get('bundle_complete') or a.record_only else 2
    except (OSError,ValueError,ELFError,subprocess.TimeoutExpired) as e:
        session.report['error']=str(e);session.persist();p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
