"""Compile a distinct destination-picture probe from exact retained evidence.
No networking, no V1 writes, no claim of a larger physical canvas.
"""
import hashlib,json,struct
from ric_lifecycle import Reader
from ric_graph import decode_graph_body,encode_description_body
from ric_destination_high import decode,encode
from road_list_expansion_trial import profile_commands,run_plan
from prepare_road_list_expansion import marker
from ric_rle32 import marker_bgra

WITNESS_SHA='46ad83e1306e4a3f35fd7dfe0b7e5ea19cecc42e4594e40738d6c49b1a1cd1b3'
ABSENT=0xffffffff

def compile_plan(profile,reply,witness):
    if hashlib.sha256(witness).hexdigest()!=WITNESS_SHA:
        raise ValueError('Exact retained factory destination witness required')
    from prepare_road_list_expansion import limits
    limits(reply)
    r=Reader(reply[16:]);handle=r.u32();items=Reader(r.take(r.u32()));r.finish();destination=None
    while items.pos<len(items.data):
        n,tag=items.u32(),items.u32();raw=items.take(n)
        if tag==1 and len(raw)==10 and raw[1]==49:
            if destination is not None:raise ValueError('Duplicate destination configuration')
            kind,typ,count,offset=struct.unpack('>BBII',raw)
            if (kind,typ,count,offset)!=(1,49,5,0x31000000):raise ValueError('Destination allocation differs')
            destination=offset+count-1
    if handle!=200 or destination is None:raise ValueError('Destination model not advertised')
    w=json.loads(witness);high=decode(bytes.fromhex(w['high']))
    if (high['model_type'],high['maneuver_type'],high['stopover_number'],high['picture_resource_id'])!=(49,0,0,ABSENT):
        raise ValueError('Unexpected factory destination state')
    setup,cleanup=profile_commands(profile,'control')
    def remap(body,typ,mid):
        b=bytearray.fromhex(body)
        if b[8]!=typ or b[21]!=typ or b[4:8]!=b[17:21]:raise ValueError('Malformed factory support identity')
        b[4:8]=struct.pack('>I',mid);b[17:21]=struct.pack('>I',mid)
        return bytes(b)
    # Preserve actual factory current-state and zero-distance payloads.
    setup[1]=(10,remap(w['current'],34,0x22000004))
    setup[2]=(10,remap(w['distance'],29,0x1d00001d))
    high.update(model_id=destination,picture_resource_id=0x01000009)
    setup[3]=(11,encode(**high))
    d=decode_graph_body(10,bytes.fromhex(w['description']))['description']
    if d['maneuver_direction']!=10 or d['detailed_maneuver_id']!=0x31000000:raise ValueError('Factory graph does not bind destination')
    d.pop('outer_identity_matches');d.update(handle=200,model_id=0x0f000004,
        previous_joined=False,previous_maneuver_id=ABSENT,next_joined=False,next_maneuver_id=ABSENT,
        coming_road_id=0x27000004,current_state_id=0x22000004,detailed_maneuver_id=destination,distance_id=0x1d00001d)
    setup[5]=(10,encode_description_body(**d))
    absent=dict(high,picture_resource_id=ABSENT)
    # Cancel, idle, and detach the list BEFORE removing the new picture reference.
    cleanup.insert(3,(11,encode(**absent)))
    return dict(case='destination_picture',model_type=49,model_id=destination,
        setup=setup,cleanup=cleanup,
        images=[(0x01000008,150,36,marker(1)),(0x01000009,150,36,marker_bgra(150,36))],
        factory_witness_sha256=WITNESS_SHA,source_pcap_sha256=w['pcap_sha256'],
        visible_seconds=30,larger_area_proven=False,receiver_pixels_verified=False)

def run(session,plan,record,observe,begin_cleanup=lambda:None):
    if session.allocation['models'].get(49)!=plan['model_id']:
        raise ValueError('Destination model admission missing')
    return run_plan(session,plan['setup'],plan['cleanup'],plan['images'],plan['case'],record,observe,begin_cleanup)
