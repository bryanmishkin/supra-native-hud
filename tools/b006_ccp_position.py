"""Offline B006 model30/tag4 codec; no ownership or live execution permission."""
import struct

ABSENT=0xffffffff

def encode(handle,model_id,center,picture_resource_id,orientation):
    for value in(handle,model_id,picture_resource_id):
        if type(value)is not int or not 0<=value<=0xffffffff:raise ValueError('u32 required')
    if len(center)!=2 or any(type(v)is not int or not 0<=v<=65535 for v in center):raise ValueError('Two u16 coordinates required')
    if type(orientation)is not int or not 0<=orientation<=65535:raise ValueError('u16 orientation required')
    payload=struct.pack('>IBHHIH',model_id,30,center[0],center[1],picture_resource_id,orientation)
    return struct.pack('>IIBII',handle,model_id,30,15,4)+payload

def decode(body):
    if not isinstance(body,bytes) or len(body)!=32:raise ValueError('Expected exact32byte control body')
    handle,model,kind,size,tag=struct.unpack('>IIBII',body[:17])
    inner,inner_kind,x,y,picture,orientation=struct.unpack('>IBHHIH',body[17:])
    if(kind,size,tag,inner,inner_kind)!=(30,15,4,model,30):raise ValueError('Control identity or variant mismatch')
    return dict(handle=handle,model_id=model,center=[x,y],picture_resource_id=picture,
        orientation=orientation,live_admission_proven=False,removal_proven=False)

def without_picture(body):
    """Remove only this encoded picture reference, NOT confirmed remote removal."""
    d=decode(body)
    return encode(d['handle'],d['model_id'],d['center'],ABSENT,d['orientation'])
