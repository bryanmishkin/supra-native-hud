"""Offline B006 method-11 codec. No transport or session allocation.

Tag 7 is the factory RoundaboutHighElement picture reference, not a free-form
surface. Evidence and address chain: RIC-GUIDING-BINDING.md.
"""
import hashlib
import struct
from ric_lifecycle import Reader, MAX_BODY


def decode_guiding_body(body):
    r = Reader(body)
    handle, model_id = r.u32(), r.u32()
    model_type = r.take(1)[0]
    if model_type > 50:
        raise ValueError('Invalid model type')
    size, tag = r.u32(), r.u32()
    payload = r.take(size)
    r.finish()
    result = dict(handle=handle, model_id=model_id, model_type=model_type,
                  variant_tag=tag, payload_bytes=size,
                  payload_sha256=hashlib.sha256(payload).hexdigest(),
                  windshield_binding_proven=False, live_drawing_allowed=False)
    if tag == 0 and payload:
        raise ValueError('Empty variant has payload')
    if tag == 7:
        if len(payload) != 11:
            raise ValueError('Expected 11-byte high-roundabout model')
        inner_id, inner_type, maneuver, direction, picture = struct.unpack('>IBBBI', payload)
        if inner_type > 50 or maneuver > 5 or direction not in (1, 2):
            raise ValueError('Invalid high-roundabout enum')
        result['high_roundabout'] = dict(model_id=inner_id, model_type=inner_type,
            maneuver_type=maneuver, drive_direction=direction,
            picture_resource_id=picture,
            outer_identity_matches=(inner_id == model_id and inner_type == model_type))
    return result


def decode_guiding_packet(packet):
    if not isinstance(packet, bytes) or not 16 <= len(packet) <= MAX_BODY + 16:
        raise ValueError('Invalid packet size')
    svc, method, length, client, session, protocol, interface, kind, code = struct.unpack(
        '>HHIHHBBBB', packet[:16])
    if (svc, method, protocol, interface, kind, code) != (0xb006, 11, 1, 1, 0, 0):
        raise ValueError('Expected B006 method-11 interface-1 request')
    if length != len(packet) - 8:
        raise ValueError('Invalid SOME/IP length')
    result = decode_guiding_body(packet[16:])
    result.update(client=client, session=session)
    return result


def encode_high_roundabout_body(handle, model_id, model_type, maneuver_type,
                                 drive_direction, picture_resource_id):
    """Encode explicit synthetic fields; no default factory identifiers.

    A correct body does not establish a visible graph or an owned resource.
    Enum names beyond the logged field names remain unassigned.
    """
    for value in (handle, model_id, picture_resource_id):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('Expected u32 identifier')
    for value, allowed in ((model_type, range(51)), (maneuver_type, range(6)),
                           (drive_direction, (1, 2))):
        if type(value) is not int or value not in allowed:
            raise ValueError('Invalid model enum')
    payload = struct.pack('>IBBBI', model_id, model_type, maneuver_type,
                          drive_direction, picture_resource_id)
    return struct.pack('>IIBII', handle, model_id, model_type, len(payload), 7) + payload


def encode_empty_guiding_body(handle, model_id, model_type):
    """Tag0 has no member payload (controller bc0fa4..bc0ff0).

    This is an encoded empty union, not proof of server-side deletion or hiding.
    """
    for value in (handle,model_id):
        if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Expected u32 identifier')
    if type(model_type) is not int or not 0<=model_type<=50:raise ValueError('Invalid model type')
    return struct.pack('>IIBII',handle,model_id,model_type,0,0)
