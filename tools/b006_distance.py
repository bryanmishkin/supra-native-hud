"""Offline model29 distance codec. Numeric changes do not prove HUD routing."""
import math,struct

def decode(body):
    if not isinstance(body,bytes) or not 48<=len(body)<=4096:raise ValueError('Invalid bounded body')
    handle,model,kind,size,tag=struct.unpack('>IIBII',body[:17])
    if(kind,tag,size)!=(29,4,len(body)-17):raise ValueError('Expected distance model29/tag4')
    inner,inner_kind,bar,distance=struct.unpack('>IBBd',body[17:31])
    if(inner,inner_kind)!=(model,kind) or not math.isfinite(distance):raise ValueError('Identity/nonfinite distance')
    at=31
    def vector():
        nonlocal at
        if at+4>len(body):raise ValueError('Missing vector length')
        n=struct.unpack_from('>I',body,at)[0];at+=4
        if n>len(body)-at:raise ValueError('Truncated vector')
        result=body[at:at+n];at+=n;return result
    segments=vector();text=vector()
    if at+9!=len(body):raise ValueError('Invalid distance tail')
    unit,arrival=struct.unpack('>BQ',body[at:])
    if unit>5:raise ValueError('Unknown unit enum')
    return dict(handle=handle,model_id=model,bar_graph_value=bar,distance=distance,
        bar_graph_segmentation=segments,distance_text_wire=text,unit=unit,expected_arrival_time=arrival)

def encode(d):
    payload=struct.pack('>IBBd',d['model_id'],29,d['bar_graph_value'],d['distance'])
    for name in('bar_graph_segmentation','distance_text_wire'):
        v=d[name]
        if not isinstance(v,bytes):raise ValueError('Opaque wire bytes required')
        payload+=struct.pack('>I',len(v))+v
    payload+=struct.pack('>BQ',d['unit'],d['expected_arrival_time'])
    body=struct.pack('>IIBII',d['handle'],d['model_id'],29,len(payload),4)+payload
    decode(body);return body

def replace_distance(body,value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=10000:
        raise ValueError('Bounded finite distance0..10000 required')
    d=decode(body);d['distance']=float(value);result=encode(d)
    if result[:23]!=body[:23] or result[31:]!=body[31:]:raise ValueError('Unexpected unrelated mutation')
    return result
