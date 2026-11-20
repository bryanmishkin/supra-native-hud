#!/usr/bin/env python3
"""Compare saved positive/negative road-image transactions; never contacts a car."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from ric_road_list import decode as road_decode
from ric_resource import decode_resource_packet


def read_requests(folder):
    rows=[]
    for path in sorted(folder.glob('*-request.bin')):
        packet=path.read_bytes()
        if len(packet)<16:raise ValueError('Short request: '+str(path))
        svc,method,n,client,session,pv,iv,kind,rc=struct.unpack('>HHIHHBBBB',packet[:16])
        if n!=len(packet)-8 or (svc,pv,iv,kind,rc)!=(0xb006,1,1,0,0):
            raise ValueError('Unexpected request envelope: '+str(path))
        rows.append(dict(file=path.name,method=method,body=packet[16:],packet=packet))
    if not rows:raise ValueError('No saved requests: '+str(folder))
    return rows


def compare(root):
    cases={};raw={}
    for case in ['control','two_icons_one_entry','one_icon_two_entries']:
        rows=read_requests(root/case);raw[case]=rows
        resources=[dict(file=r['file'],**decode_resource_packet(r['packet']))for r in rows if r['method']==3]
        roads=[dict(file=r['file'],**road_decode(r['body']))for r in rows if r['method']==14]
        graph=[r for r in rows if r['method']in (4,9,10,11,12,13,14)]
        result=json.loads((root/case/'result.json').read_text())
        cases[case]=dict(resources=resources,roads=roads,graph_messages=len(graph),
                         cleanup_passed=result.get('protocol_cleanup_passed'),
                         request_sha256={r['file']:hashlib.sha256(r['packet']).hexdigest()for r in rows})
    a,b=(raw[c]for c in ['two_icons_one_entry','one_icon_two_entries'])
    uploads=lambda rows:[r['body']for r in rows if r['method']==3]
    graph=lambda rows:[(r['method'],r['body'])for r in rows if r['method']in (4,9,10,11,12,13,14)]
    x,y=graph(a),graph(b)
    if len(x)!=len(y):raise ValueError('Different graph counts; manual correlation required')
    changed=[]
    for index,(left,right) in enumerate(zip(x,y)):
        if left!=right:
            changed.append(dict(graph_index=index,methods=[left[0],right[0]],body_lengths=[len(left[1]),len(right[1])],
                                left_road=road_decode(left[1]) if left[0]==14 else None,
                                right_road=road_decode(right[1]) if right[0]==14 else None))
    if len(a)!=len(b):raise ValueError('Different complete request counts')
    all_changes=[dict(file=l['file'],left_method=l['method'],right_method=r['method'])
                 for l,r in zip(a,b) if (l['method'],l['body'])!=(r['method'],r['body'])]
    return dict(cases=cases,comparison=dict(total_requests_per_pair=len(a),all_request_body_changes=all_changes,two_image_uploads_identical=uploads(a)==uploads(b),graph_changes=changed,
                same_other_graph_messages=all(d['methods']==[14,14]for d in changed)),
                observations_source='Owner reports and photos, not inferred from packets: control both displays; two icons in one entry cluster only; separate entries both displays with second HUD image clipped.',
                limitation='Saved direct request journals, not an all-traffic causal isolation. This proves supplied image equality and graph differences, not the receiver implementation, optical boundary, or local MapCanvas linkage.',vehicle_contact=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('session',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    r=compare(a.session);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['comparison'],indent=2))
