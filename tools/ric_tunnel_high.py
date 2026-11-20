"""Strict offline B006 method11 tunnel-high variant8 codec; not live admission."""
import math
import struct
from ric_branch_high import encode as validate_identity

def encode(handle, model_id, model_type, maneuver_type, length, length_text, unit, picture_resource_id):
    validate_identity(handle, model_id, 3, maneuver_type, picture_resource_id)
    if type(model_type) is not int or model_type != 13:
        raise ValueError('Tunnel requires model type13')
    if type(length) not in (int, float) or not math.isfinite(length) or length < 0:
        raise ValueError('Length must be finite and nonnegative')
    if type(unit) is not int or not 0 <= unit <= 5:
        raise ValueError('Invalid unit enum')
    if not isinstance(length_text, str) or '\0' in length_text or len(length_text) > 128:
        raise ValueError('Invalid length text')
    raw = b'\xfe\xff' + length_text.encode('utf-16-be') + b'\0\0'
    payload = struct.pack('>IBBdI', model_id, model_type, maneuver_type, length, len(raw)) + raw + struct.pack('>BI', unit, picture_resource_id)
    return struct.pack('>IIBII', handle, model_id, model_type, len(payload), 8) + payload

def decode(body):
    if not isinstance(body, bytes) or len(body) < 44:
        raise ValueError('Truncated tunnel body')
    handle, oid, ot, size, tag = struct.unpack('>IIBII', body[:17])
    mid, mt, maneuver, length, n = struct.unpack('>IBBdI', body[17:35])
    if tag != 8 or size != len(body)-17 or (oid,ot)!=(mid,mt) or n < 4 or n%2 or len(body)!=40+n:
        raise ValueError('Invalid tunnel identity or extent')
    raw=body[35:35+n]
    if raw[:2]!=b'\xfe\xff' or raw[-2:]!=b'\0\0':raise ValueError('Invalid string framing')
    unit,picture=struct.unpack('>BI',body[35+n:])
    result=dict(handle=handle,model_id=mid,model_type=mt,maneuver_type=maneuver,length=length,length_text=raw[2:-2].decode('utf-16-be'),unit=unit,picture_resource_id=picture)
    if encode(**result)!=body:raise ValueError('Noncanonical tunnel body')
    return result
