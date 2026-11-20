"""Strict B006 method11 branch-high variant5 codec; offline, no admission."""
import struct

def encode(handle, model_id, model_type, maneuver_type, picture_resource_id):
    for value in (handle, model_id, picture_resource_id):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('Identifier must be u32')
    if type(model_type) is not int or model_type != 3:
        raise ValueError('Invalid model type')
    if type(maneuver_type) is not int or not 0 <= maneuver_type <= 5:
        raise ValueError('Invalid maneuver type')
    payload = struct.pack('>IBBI', model_id, model_type, maneuver_type, picture_resource_id)
    return struct.pack('>IIBII', handle, model_id, model_type, len(payload), 5) + payload

def decode(body):
    if not isinstance(body, bytes) or len(body) != 27:
        raise ValueError('Expected complete 27-byte branch-high body')
    handle, outer_id, outer_type, size, tag = struct.unpack('>IIBII', body[:17])
    model_id, model_type, maneuver_type, picture = struct.unpack('>IBBI', body[17:])
    if size != 10 or tag != 5 or (outer_id, outer_type) != (model_id, model_type):
        raise ValueError('Variant or inner/outer identity mismatch')
    result = dict(handle=handle, model_id=model_id, model_type=model_type,
                  maneuver_type=maneuver_type, picture_resource_id=picture)
    if encode(**result) != body:
        raise ValueError('Invalid branch-high body')
    return result
