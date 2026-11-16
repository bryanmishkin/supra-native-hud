#!/usr/bin/env python3
"""Bounded, read-only OMAP capture. Default mode prints the plan; no network access."""
import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import subprocess

LIBRARIES = ('libc.so.3', 'libm.so.2', 'libsocket.so.3', 'libstdc++.so.6',
             'libgcc_s.so.1', 'libsys_dsi_base.cpp-ne.so.4',
             'libsys_dsi_colibry.cpp-ne.so.8',
             'libsys_colibry.cpp-ne.so.7', 'libbacktrace.so.1',
             'libsys_colibry_net.cpp-ne.so.7', 'libsys_trace_clienttrace.cpp-ne.so.7',
             'libsys_dsi_servicebroker.cpp-ne.so.4', 'libsys_dsi_trace.cpp-ne.so.6',
             'libcpp-ne.so.4')
DIRECTORIES = ('/lib', '/usr/lib', '/boot/lib', '/proc/boot', '/opt/sys/lib', '/opt/hmi/ID5/lib', '/opt/car/lib')
READS = {'platform': 'uname -a', 'loader-path': 'getconf CS_LIBPATH',
         'processes': 'pidin ar', 'interfaces': '/sbin/ifconfig -a', 'routes': 'netstat -rn',
         'plugin-paths': 'ls -ld /var/opt/hmi/data/ID5/Plugins /opt/hmi/ID5/data/ro/Plugins /opt/hmi/ID5/data/ro/PluginsCoded /opt/hmi/ID5/data/ro/hmiplugins',
         'factory-manifests': 'find /opt/hmi/ID5/data/ro/PluginsCoded /opt/hmi/ID5/data/ro/hmiplugins -type f -name "*.manifest" -exec cat {} \\;',
         'custom-manifests': 'find /var/opt/hmi/data/ID5/Plugins -type f -name "*.manifest" -exec cat {} \\;'}
LIMIT = 16 * 1024 * 1024

def link_local(value):
    ip = ipaddress.IPv4Address(value)
    if not ip.is_link_local or ip.packed[2] in (0,255):
        raise argparse.ArgumentTypeError('Expected wired 169.254.x.x address')
    return str(ip)

def plan():
    return {'target': 'Direct SSH to verified hu-omap only; no Jacinto Qnet fallback',
            'commands': READS, 'libraries': LIBRARIES, 'search_directories': DIRECTORIES,
            'remote_writes': False, 'max_library_bytes': LIMIT,
            'limits': 'No activation, installation, registry access, HUD rendering or ECU requests.'}

def ssh_args(a, command):
    return ['ssh', '-T', '-b', a.local, '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=5',
            '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2',
            '-o', 'UserKnownHostsFile='+str(a.known_hosts.resolve()),
            '-o', 'HostKeyAlgorithms=+ssh-rsa',
            '-o', 'KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1',
            '-o', 'Ciphers=+aes128-cbc',
            *(['-S', str(a.socket.resolve())] if a.socket else []),
            'root@'+a.head, command]

def run(a):
    a.output.mkdir(parents=True, exist_ok=False)
    log=[]
    def read(command):
        try:
            r=subprocess.run(ssh_args(a,command),capture_output=True,timeout=30)
            record={'command':command,'status':r.returncode,'bytes':len(r.stdout),
                    'stderr':r.stderr.decode(errors='replace')[:2000]}
            data=r.stdout
        except subprocess.TimeoutExpired:
            record={'command':command,'status':'timeout'};data=b''
        log.append(record)
        (a.output/'capture-log.json').write_text(json.dumps(log,indent=2))
        return record,data
    status,platform=read(READS['platform'])
    if status['status']!=0 or b'hu-omap' not in platform or b'armle' not in platform or not platform.startswith(b'QNX'):
        raise SystemExit('Stopped: direct ARM QNX hu-omap identity not verified')
    (a.output/'platform.txt').write_bytes(platform)
    for name,command in READS.items():
        if name=='platform':continue
        status,data=read(command)
        if len(data)>LIMIT:raise SystemExit('Stopped: oversized text response')
        (a.output/(name+'.txt')).write_bytes(data)
    manifest=[]
    for library in LIBRARIES:
        found=False
        for directory in DIRECTORIES:
            remote=directory+'/'+library
            # One extra byte distinguishes a capped response from a complete <=16 MiB file.
            command='dd if='+remote+' bs=65536 count=257'
            status,data=read(command)
            if status['status']!=0:continue
            if len(data)>LIMIT:raise SystemExit('Stopped: oversized library '+remote)
            if data[:6]!=b'\x7fELF\x01\x01':continue
            status,again=read(command)
            if status['status']!=0 or again!=data:raise SystemExit('Stopped: inconsistent repeated read '+remote)
            (a.output/library).write_bytes(data)
            manifest.append({'name':library,'remote_path':remote,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'repeat_read_matched':True})
            found=True;break
        if not found:manifest.append({'name':library,'status':'not captured; inspect command log'})
        (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--head',type=link_local)
    p.add_argument('--local',type=link_local)
    p.add_argument('--known-hosts',type=Path)
    p.add_argument('--socket',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:print(json.dumps(plan(),indent=2));return
    if not all((a.head,a.local,a.known_hosts,a.output)):p.error('Execution requires --head, --local, --known-hosts and --output')
    if not a.known_hosts.is_file():p.error('Known-hosts file is missing')
    run(a)
if __name__=='__main__':main()
