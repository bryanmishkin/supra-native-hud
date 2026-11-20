#!/usr/bin/env python3
"""Build an offline two-image road-list geometry kit. Never connects to a car."""
import argparse,hashlib,json,struct
from pathlib import Path
from ric_lifecycle import Reader
from ric_road_list import decode,two_image_candidates
from ric_resource import encode_bitmap_body
from ric_rle32 import encode_bgra


def limits(packet):
    if len(packet)<24 or packet[:4]!=bytes.fromhex('b0060001') or packet[12:16]!=bytes([1,1,128,0]) or int.from_bytes(packet[4:8],'big')!=len(packet)-8:
        raise ValueError('Expected successful B006 create reply')
    r=Reader(packet[16:]);handle=r.u32();items=Reader(r.take(r.u32()));r.finish();road=None
    while items.pos<len(items.data):
        n,tag=items.u32(),items.u32();raw=items.take(n)
        if tag==30:
            if road is not None or len(raw)!=20:raise ValueError('Ambiguous road config')
            kind,model,count,offset,entries,icons,texts,w,h=struct.unpack('>BBIIHHHHH',raw)
            if (kind,model)!=(30,40):raise ValueError('Wrong model config')
            road=dict(model_count=count,model_offset=offset,max_entries=entries,max_icons=icons,max_texts=texts,max_icon_size=[w,h])
    if handle!=200 or road is None or road['max_entries']<2 or road['max_icons']<2 or road['max_icon_size']!=[150,36]:
        raise ValueError('Unsupported retained profile')
    return road


def marker(number):
    glyphs={1:['010','110','010','010','111'],2:['111','001','111','100','111']}
    color=(255,200,0,255) if number==1 else (0,160,255,255) # canonical BGRA cyan/amber
    raw=bytearray()
    for y in range(36):
        for x in range(150):
            border=x in (1,148) or y in (1,34)
            gx,gy=(x-66)//5,(y-5)//5
            digit=0<=gx<3 and 0<=gy<5 and glyphs[number][gy][gx]=='1'
            raw.extend(color if border or digit else (0,0,0,255))
    return bytes(raw)


def prepare(reply,control,out):
    config=limits(reply);value=decode(control)
    if value['handle']!=200 or not config['model_offset']<=value['model_id']<config['model_offset']+config['model_count']:
        raise ValueError('Control outside advertised model range')
    if any(e['trailing_bytes']!=[0,0] for e in value['entries']):raise ValueError('Only observed zero row fields admitted')
    candidates=two_image_candidates(control,0x01000008,0x01000009)
    out.mkdir(parents=True,exist_ok=False)
    for label,body in candidates.items():(out/(label+'.body')).write_bytes(body)
    for n,rid in [(1,0x01000008),(2,0x01000009)]:
        raw=marker(n);(out/f'marker-{n}.bgra').write_bytes(raw)
        # Same V1 display-channel correction, applied exactly once.
        from ric_rle32 import swap_red_blue
        image=encode_bgra(swap_red_blue(raw))
        (out/f'upload-{n}.body').write_bytes(encode_bitmap_body(200,rid,1,[150,36],image))
    (out/'control.body').write_bytes(control)
    manifest=dict(configuration=config,create_sha256=hashlib.sha256(reply).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(out.iterdir())},
        vehicle_contact=False,requires_current_car_admission=True,visible_layout_proven=False,
        purpose='Measure two supported road images within one entry versus two entries; no PiP, no Hz tests.',
        required_before_live=['Current V1 hash check and cooperative pause','Both image slots absent','Bounded runner with acknowledged withdrawal then removal of both images','V1 restoration and runtime verification'],
        observations=['Count visible numbered images separately in windshield and cluster','Record side-by-side, stacked, overlap or clipping; never infer from ACK','Confirm both images removed'])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--create-reply',type=Path,required=True);p.add_argument('--control-body',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=prepare(a.create_reply.read_bytes(),a.control_body.read_bytes(),a.output)
    print(json.dumps({k:r[k]for k in ('configuration','requires_current_car_admission','visible_layout_proven')}))
