#!/usr/bin/env python3
"""Offline B006 resource codec derived from the saved controller.

No sockets, endpoint, factory handle, or live sender. Encoding a bitmap body
proves its format only; it neither allocates a resource nor makes it visible.
"""
import hashlib
import struct
from ric_lifecycle import Reader, MAX_BODY

SET_RESOURCE = 3
BITMAP_TAG = 2


def decode_resource_body(body):
    r = Reader(body)
    handle, resource_id = r.u32(), r.u32()
    resource_type = r.take(1)[0]
    if resource_type > 11:
        raise ValueError('Invalid resource type enum')
    size, tag = r.u32(), r.u32()
    payload = r.take(size)
    r.finish()
    result = dict(handle=handle, resource_id=resource_id, resource_type=resource_type,
                  variant_tag=tag, payload_bytes=size,
                  payload_sha256=hashlib.sha256(payload).hexdigest(),
                  resource_ownership_proven=False, windshield_binding_proven=False,
                  live_drawing_allowed=False)
    if tag == 0 and payload:
        raise ValueError('Empty variant has a payload')
    if tag == BITMAP_TAG:
        b = Reader(payload)
        inner_id = b.u32()
        inner_type = b.take(1)[0]
        if inner_type > 11:
            raise ValueError('Invalid inner resource type enum')
        pair = list(struct.unpack('>HH', b.take(4)))
        image = b.take(b.u32())
        b.finish()
        result['bitmap'] = dict(resource_id=inner_id, resource_type=inner_type,
                                resolution_pair=pair, image_bytes=len(image),
                                image_sha256=hashlib.sha256(image).hexdigest(),
                                outer_identity_matches=(inner_id == resource_id and
                                                        inner_type == resource_type))
    return result


def decode_resource_packet(packet):
    if not isinstance(packet, bytes) or not 16 <= len(packet) <= MAX_BODY + 16:
        raise ValueError('Invalid packet size')
    svc, method, length, client, session, protocol, interface, kind, code = struct.unpack(
        '>HHIHHBBBB', packet[:16])
    if (svc, method, protocol, interface, kind, code) != (0xb006, 3, 1, 1, 0, 0):
        raise ValueError('Expected B006 method-3 interface-1 request')
    if length != len(packet) - 8:
        raise ValueError('Invalid SOME/IP length')
    result = decode_resource_body(packet[16:])
    result.update(client=client, session=session)
    return result


def encode_bitmap_body(handle, resource_id, resource_type, resolution_pair, image):
    """Serialize a test body, not a packet or a sendable session transaction.

    Enum meaning/format support must come from actual negotiated configuration.
    Resolution axis names deliberately remain unspecified. No defaults select
    factory state. The common inner identity mirrors the outer arguments.
    """
    for value in (handle, resource_id):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('Expected u32 identity')
    if type(resource_type) is not int or not 0 <= resource_type <= 11:
        raise ValueError('Expected resource enum 0..11')
    if not isinstance(resolution_pair, (list, tuple)) or len(resolution_pair) != 2:
        raise ValueError('Expected two resolution values')
    if any(type(v) is not int or not 0 <= v <= 65535 for v in resolution_pair):
        raise ValueError('Expected u16 resolution values')
    if not isinstance(image, bytes) or len(image) > MAX_BODY - 30:
        raise ValueError('Expected bounded image bytes')
    payload = struct.pack('>IBHHI', resource_id, resource_type,
                          *resolution_pair, len(image)) + image
    return struct.pack('>IIBII', handle, resource_id, resource_type,
                       len(payload), BITMAP_TAG) + payload
