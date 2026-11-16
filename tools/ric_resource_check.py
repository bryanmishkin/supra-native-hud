"""Offline resource-check codec and distinct-client create-body preparation.

No network operations. A Boolean result is not proof of windshield erasure;
a distinct identity string is not proof of server acceptance or ownership.
"""
import struct
from ric_lifecycle import Reader, MAX_BODY, MAX_STRING_BYTES


def encode_check_body(handle, resource_id, resource_type):
    for v in (handle, resource_id):
        if type(v) is not int or not 0 <= v <= 0xffffffff:
            raise ValueError('Expected u32 identifier')
    if type(resource_type) is not int or not 0 <= resource_type <= 11:
        raise ValueError('Invalid resource type')
    return struct.pack('>IIB', handle, resource_id, resource_type)


def decode_check_packet(packet):
    if not isinstance(packet, bytes) or not 16 <= len(packet) <= MAX_BODY + 16:
        raise ValueError('Invalid packet size')
    svc, method, n, client, session, proto, interface, kind, code = struct.unpack('>HHIHHBBBB', packet[:16])
    if (svc, method, proto, interface) != (0xb006, 2, 1, 1) or n != len(packet)-8:
        raise ValueError('Expected complete B006 method-2 packet')
    if kind not in (0, 0x80, 0x81) or (kind == 0 and code != 0):
        raise ValueError('Invalid message kind/code')
    result = dict(client=client, session=session, message_type=kind, return_code=code,
                  remote_cleanup_proven=False)
    r = Reader(packet[16:])
    if kind == 0:
        result['handle'], result['resource_id'] = r.u32(), r.u32()
        result['resource_type'] = r.take(1)[0]
        if result['resource_type'] > 11:
            raise ValueError('Invalid resource type')
    elif kind == 0x80 and code == 0:
        value = r.take(1)[0]
        if value > 1:
            raise ValueError('Invalid Boolean reply')
        result['check_result'] = bool(value)
    else:
        # Error payloads are not the successful Boolean schema. Never turn
        # an empty/error reply into false (or infer resource disappearance).
        result['error_payload_bytes'] = len(r.take(len(packet)-16))
        result['check_result'] = None
    r.finish()
    return result


def encode_distinct_create_body(identity_strings, version_words):
    """Prepare explicit candidate identity; no guessed protocol version.

    Reject the two known factory roles, without claiming that other strings
    are accepted or unused by the server. Version words must be supplied from
    a justified contract; they are not automatically the app's version.
    """
    if not isinstance(identity_strings, (tuple, list)) or len(identity_strings) != 3:
        raise ValueError('Expected three identity strings')
    if identity_strings[0] in ('BMW.IC.Guidance', 'BMW.HMI.Roadbook'):
        raise ValueError('Factory identity cannot be used for the distinct-client test')
    parts=[]
    for value in identity_strings:
        if not isinstance(value, str) or not value or any(not 32 <= ord(c) <= 126 for c in value):
            raise ValueError('Expected nonempty printable ASCII identity')
        if len(value) > (MAX_STRING_BYTES-4)//2:
            raise ValueError('Identity too long')
        raw=b'\xfe\xff'+value.encode('utf-16-be')+b'\0\0'
        parts.append(struct.pack('>I',len(raw))+raw)
    if not isinstance(version_words, (tuple,list)) or len(version_words) != 3:
        raise ValueError('Expected three explicit version words')
    for v in version_words:
        if type(v) is not int or not 0 <= v <= 0xffffffff:
            raise ValueError('Expected u32 version word')
    return b''.join(parts)+struct.pack('>III',*version_words)
