#!/usr/bin/env python3
"""Decode first retained HGPictureInPicture chunks; never replay shared memory."""
import argparse,collections,hashlib,json,struct
from pathlib import Path
from inspect_gv_buffer import inspect

def decode(data):
    info=inspect(data)
    first=info['chunks'][0]
    if first['type']!='0x70008':return None
    if first['payload_bytes']!=12:raise ValueError('Expected native 12-byte HGPictureInPicture payload')
    maneuver,resource,width,height,depth,packing,picture=struct.unpack_from('<BBHHBBI',data,20)
    return {'snapshot_sha256':info['sha256'],'payload_sha256':first['payload_sha256'],
            'sequence':info['sequence'],'reusable':info['reusable'],
            'maneuver_type':maneuver,'resource_type':resource,'width':width,'height':height,
            'depth':depth,'packing':packing,'picture_id':picture,
            'active_frame_proven':False,'windshield_destination_proven':False,
            'scope':'first retained chunk only; not an event-bounded or atomic frame'}

def audit(root):
    snapshots={};errors=[];files=0;matches=0
    for path in sorted(root.rglob('GVCommand*.bin')):
        files+=1
        try:
            if path.stat().st_size>262144:raise ValueError('snapshot exceeds bound')
            row=decode(path.read_bytes())
        except (ValueError,OSError) as e:errors.append({'path':str(path),'error':str(e)});continue
        if row is None:continue
        matches+=1;key=row['snapshot_sha256']
        if key not in snapshots:snapshots[key]={'decoded':row,'paths':[]}
        snapshots[key]['paths'].append(str(path))
    counts=collections.Counter((r['decoded']['width'],r['decoded']['height'],r['decoded']['depth'],r['decoded']['packing']) for r in snapshots.values())
    return {'files_considered':files,'matching_file_copies':matches,'unique_matching_snapshots':len(snapshots),
            'unique_snapshot_geometry_counts':[{'width':k[0],'height':k[1],'depth':k[2],'packing':k[3],'count':v} for k,v in sorted(counts.items())],
            'snapshots':snapshots,'errors':errors,'vehicle_contact':False,'larger_display_ready':False,
            'limitation':'Retained reusable bytes may predate capture; directory phase is not display-time proof. No main surface or receiver association inferred.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('corpus',type=Path)
    print(json.dumps(audit(p.parse_args().corpus),indent=2))
