#!/usr/bin/env python3
"""Read-only, bounded, operator-staged factory displayable inventory.

Does not reboot, activate SSH, alter boot state, send SOME/IP requests, or draw.
Default is a dry-run plan. Captures are privately stored on the Mac.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import time
from pathlib import Path

GV = re.compile(r'^GVCommand_(\d+)_(\d+)_(\d+)$')
LIMIT_FILE = 131072
LIMIT_TOTAL = 32 * 1024 * 1024
LIMIT_ITEMS = 128
STAGES = ('baseline', 'hud-height-bottom', 'hud-height-middle', 'hud-height-top',
          'radio-open', 'radio-closed', 'speed-limit-visible', 'speed-limit-hidden',
          'navigation-visible', 'navigation-hidden', 'pip-graphic-visible',
          'hud-calibration-visible', 'hud-calibration-hidden', 'other')


def parse_listing(listing):
    """Only specifically sized GVCommand objects under known nav directory."""
    rows = []
    for line in listing.splitlines():
        cols = line.split()
        if len(cols) < 9:
            continue
        m = GV.fullmatch(cols[-1])
        if not m:
            continue
        size = int(cols[4]) if cols[4].isdigit() else -1
        if not 20 <= size <= LIMIT_FILE or size != int(m.group(3)):
            continue
        rows.append(dict(name=cols[-1], displayable_id=int(m.group(1)),
                         slot=int(m.group(2)), bytes=size))
    if len(rows) > LIMIT_ITEMS:
        raise ValueError('GVCommand object count exceeds safe limit')
    return sorted(rows, key=lambda x:(x['displayable_id'], x['slot'], x['name']))


def summarize_gv(data):
    if len(data) < 20:
        return {'valid':False,'reason':'too short'}
    sequence = struct.unpack_from('<I', data, 8)[0]
    kind, n = struct.unpack_from('<II', data, 12)
    if n > len(data)-20:
        return {'valid':False,'reason':'invalid first chunk','sequence':sequence}
    result = dict(valid=True, sequence=sequence, reusable=sequence==0xFFFFFFFE,
                  first_chunk_kind=hex(kind), first_chunk_bytes=n)
    if kind == 0x70008 and n == 12:
        payload = data[20:32]
        result['pip_header_hex'] = payload.hex()
        result['pip_words_le16'] = list(struct.unpack('<HHHH',payload[:8]))
        result['pip_tail_le32'] = struct.unpack('<I',payload[8:])[0]
        result['pip_geometry_verified'] = False
    return result


def sha(data): return hashlib.sha256(data).hexdigest()


def session_plan():
    return {'mode':'no network unless --execute','stages':STAGES,
            'action':'Read-only snapshots of all currently listed factory GVCommand buffers plus process/network/config metadata',
            'captures': ['uname -a','pidin ar','netstat -an','ifconfig vlan73',
                         'ls -l /opt/nav/eceusa/bin','dd from selected GVCommand names','dd /etc/someip/services.conf'],
            'one_operator_set_state_per_stage':True,
            'caveats':['No autonomous HUD menus or ignition changes',
                       'Reusable GVCommand data may be stale; snapshots are not atomic',
                       'No inferred full HUD dimensions or ownership',
                       'Capture does not substitute for a simultaneous network PCAP'],
            'limits':{'max_one_buffer':LIMIT_FILE,'max_buffers':LIMIT_ITEMS,
                      'max_session_bytes':LIMIT_TOTAL,'samples':(1,3)}}


def run(a, ssh=None):
    if a.output.exists(): raise ValueError('Output directory exists; refusing to overwrite')
    if not a.known_hosts.is_file(): raise ValueError('Verified known-hosts file required')
    a.output.mkdir(parents=True)
    manifest = dict(schema=1,stage=a.stage,observer_note=a.note or '',start_host_epoch=time.time(),
                    commands=[],buffers=[],no_vehicle_writes=True,remote_draw_calls=0,
                    visual_state_confirmed_by_operator=False,full_canvas_proven=False)
    def save():
        tmp=a.output/'manifest.partial';tmp.write_text(json.dumps(manifest,indent=2)+'\n');tmp.replace(a.output/'manifest.json')
    def read(cmd, timeout=20):
        if ssh is None:
            from capture_runtime import ssh_args
            argv = ssh_args(a,cmd)
        else:
            argv=['ssh-fixture',cmd]
        try:
            r = (ssh(cmd,timeout) if ssh else subprocess.run(argv,capture_output=True,timeout=timeout))
        except subprocess.TimeoutExpired:
            manifest['commands'].append(dict(command=cmd,result='timeout'));save()
            raise
        data = r.stdout
        manifest['commands'].append(dict(command=cmd,exit=r.returncode,bytes=len(data),
                                         sha256=sha(data),stderr=r.stderr.decode(errors='replace')[:400]))
        save()
        if r.returncode: raise ValueError('Read command failed: '+cmd)
        if len(data)>LIMIT_TOTAL: raise ValueError('Reply exceeds session limit')
        return data
    save()
    try:
        identity=read('uname -a')
        if not identity.startswith(b'QNX hu-omap ') or b'armle' not in identity:
            raise ValueError('Wrong platform: no capture after failed QNX hu-omap identity')
        (a.output/'identity.txt').write_bytes(identity)
        for name,cmd in [('processes','pidin ar'),('sockets','netstat -an'),
                         ('interfaces','ifconfig vlan73'),('nav-directory','ls -l /opt/nav/eceusa/bin')]:
            content=read(cmd)
            if len(content)>1024*1024: raise ValueError('Unexpected large listing')
            (a.output/(name+'.txt')).write_bytes(content)
        config=read('dd if=/etc/someip/services.conf bs=4096 count=33')
        if len(config)>LIMIT_FILE:raise ValueError('Oversized services.conf')
        (a.output/'services.conf').write_bytes(config)
        listing=(a.output/'nav-directory.txt').read_text(errors='replace')
        buffers=parse_listing(listing)
        manifest['objects_discovered']=len(buffers)
        manifest['total_bytes_discovered']=sum(r['bytes'] for r in buffers)
        transferred=0
        for row in buffers:
            for sample in range(a.samples):
                if transferred+row['bytes']>LIMIT_TOTAL:raise ValueError('Total transfer budget exhausted')
                remote='/opt/nav/eceusa/bin/'+row['name']
                # QNX dd reads an explicitly identified shared-memory object. No shell glob.
                count=(row['bytes']+4095)//4096+1
                payload=read('dd if='+remote+' bs=4096 count='+str(count))
                transferred+=len(payload)
                item=dict(row,sample=sample,host_epoch=time.time(),sha256=sha(payload),
                          saved=False,expected_bytes=row['bytes'],actual_bytes=len(payload))
                if len(payload)==row['bytes']:
                    filename='gv_'+row['name']+'.%d.bin'%sample
                    (a.output/filename).write_bytes(payload)
                    item['saved']=True;item['file']=filename;item.update(summarize_gv(payload))
                manifest['buffers'].append(item);save()
            if a.interval_ms and a.samples>1:time.sleep(a.interval_ms/1000.0)
        manifest['complete']=True
        manifest['all_expected_sizes']=all(x['saved'] for x in manifest['buffers'])
        manifest['sampled_state_requires_manual_visual_evidence']=True
        manifest['finished_host_epoch']=time.time();save()
        return manifest
    except Exception as e:
        manifest['complete']=False;manifest['error']=str(e);save();raise


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--stage',choices=STAGES)
    p.add_argument('--note',default='')
    p.add_argument('--head');p.add_argument('--local')
    p.add_argument('--known-hosts',type=Path);p.add_argument('--socket',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--samples',type=int,choices=(1,2,3),default=2)
    p.add_argument('--interval-ms',type=int,choices=(0,250,500,1000),default=250)
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps(session_plan(),indent=2));return 0
    if not all([a.stage,a.head,a.local,a.known_hosts,a.output]):
        p.error('Execution requires --stage --head --local --known-hosts --output')
    from capture_runtime import link_local
    try:
        a.head,a.local=link_local(a.head),link_local(a.local)
        result=run(a)
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        p.exit(2,str(exc)+'\n')
    print(json.dumps({'stage':a.stage,'complete':result['complete'],
                      'objects':result['objects_discovered'],
                      'saved':sum(bool(x['saved']) for x in result['buffers']),
                      'output':str(a.output)},indent=2))
    return 0 if result['all_expected_sizes'] else 2
if __name__=='__main__':raise SystemExit(main())

