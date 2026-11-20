"""Strict offline model49/variant10 HighDestinationReached codec."""
import struct
from ric_branch_high import encode as validate

def encode(handle,model_id,model_type,maneuver_type,stopover_number,picture_resource_id):
    validate(handle,model_id,3,maneuver_type,picture_resource_id)
    if type(model_type) is not int or model_type != 49:raise ValueError('Expected model49')
    if type(stopover_number) is not int or not 0<=stopover_number<=65535:raise ValueError('Expected u16 stopover')
    payload=struct.pack('>IBBHI',model_id,model_type,maneuver_type,stopover_number,picture_resource_id)
    return struct.pack('>IIBII',handle,model_id,model_type,12,10)+payload

def decode(body):
    if not isinstance(body,bytes) or len(body)!=29:raise ValueError('Expected29-byte body')
    handle,oid,ot,size,tag=struct.unpack('>IIBII',body[:17])
    mid,mt,maneuver,stopover,picture=struct.unpack('>IBBHI',body[17:])
    if (oid,ot)!=(mid,mt) or (size,tag)!=(12,10):raise ValueError('Identity/variant mismatch')
    result=dict(handle=handle,model_id=mid,model_type=mt,maneuver_type=maneuver,stopover_number=stopover,picture_resource_id=picture)
    if encode(**result)!=body:raise ValueError('Invalid body')
    return result
