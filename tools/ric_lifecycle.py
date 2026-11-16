#!/usr/bin/env python3
"""Offline, strict subset of the statically traced B006 lifecycle body format.

No sockets, identity selection, allocation or drawing. Configuration variants
remain opaque: a returned handle is not proof of independent ownership.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

CREATE, INITIALIZE, DISPOSE, DISPOSE_RESOURCE = 1, 4, 7, 8
MAX_BODY = 65536
MAX_STRING_BYTES = 1024
MAX_CONFIGS = 256


class Reader:
    def __init__(self, data):
        if not isinstance(data, bytes) or len(data) > MAX_BODY:
            raise ValueError('Expected bounded bytes')
        self.data, self.pos = data, 0

    def take(self, size):
        if size < 0 or size > len(self.data) - self.pos:
            raise ValueError('Truncated body')
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def u32(self):
        return struct.unpack('>I', self.take(4))[0]

    def finish(self):
        if self.pos != len(self.data):
            raise ValueError('Unexpected trailing bytes')

    def identity(self):
        size = self.u32()
        if size < 4 or size > MAX_STRING_BYTES or size % 2:
            raise ValueError('Invalid identity string length')
        raw = self.take(size)
        if raw[:2] != b'\xfe\xff' or raw[-2:] != b'\0\0':
            raise ValueError('Expected UTF-16BE BOM and terminator')
        value = raw[2:-2].decode('utf-16-be', errors='strict')
        # Factory identity evidence is ASCII. Do not assume the converter's
        # non-BMP behavior matches standard UTF-16 for a hypothetical client.
        if any(not 32 <= ord(c) <= 126 for c in value):
            raise ValueError('Only printable ASCII identity subset verified')
        return value



def decode_bitmap_config(payload):
    """Static-derived tag-33 payload; values do not grant resource ownership.

    Tuple chain bcf154 -> bcf0c4 -> ... -> bc69f4 establishes order.
    Enum readers bc12e4/bc6570/bc60d4 establish widths and bounds.
    Resolution reader bcc138 consumes exactly two big-endian u16 values.
    """
    if not isinstance(payload, bytes) or len(payload) != 18:
        raise ValueError('Expected 18-byte bitmap configuration subset')
    kind, resource, count, offset, x, y, rle24, rle32, png, jpg = struct.unpack(
        '>BBIIHHBBBB', payload)
    if kind > 39 or resource > 11 or any(v > 1 for v in (rle24, rle32, png, jpg)):
        raise ValueError('Invalid bitmap configuration enum')
    return {'configuration_kind': kind, 'resource_type': resource,
            'resource_element_count': count, 'resource_element_offset': offset,
            'resolution_pair': [x, y],
            'formats': dict(zip(('rle24', 'rle32', 'png', 'jpg'),
                                map(bool, (rle24, rle32, png, jpg)))),
            'wire_format': 'static-derived; not observed in a create reply',
            'resource_ownership_proven': False, 'drawing_allowed': False}


def decode_body(method, message_type, return_code, body):
    if method not in (CREATE, INITIALIZE, DISPOSE, DISPOSE_RESOURCE):
        raise ValueError('Untraced lifecycle method')
    if message_type not in (0, 0x80) or return_code != 0:
        raise ValueError('Only successful request/response envelopes supported')
    r = Reader(body)
    result = {'method': method, 'message_type': message_type,
              'independent_ownership_proven': False,
              'windshield_destination_proven': False,
              'remote_cleanup_proven': False,
              'evidence': 'static-derived format; no observed create/dispose exchange'}
    if method == CREATE and message_type == 0:
        result['identity_strings'] = [r.identity() for _ in range(3)]
        result['version_words'] = [r.u32() for _ in range(3)]
    elif method == CREATE:
        result['candidate_handle'] = r.u32()
        byte_count = r.u32()
        entries = Reader(r.take(byte_count))
        configs = []
        while entries.pos < len(entries.data):
            if len(configs) >= MAX_CONFIGS:
                raise ValueError('Too many configuration variants')
            size, tag = entries.u32(), entries.u32()
            value = entries.take(size)
            configs.append({'tag': tag, 'bytes': size,
                            'sha256': hashlib.sha256(value).hexdigest()})
        result['configuration_variants'] = configs
        result['configuration_semantics_verified'] = False
    elif message_type == 0:
        result['handle'] = r.u32()
        if method == DISPOSE_RESOURCE:
            result['resource_id'] = r.u32()
    # Generated callbacks for initialize/dispose/disposeResource do not read
    # a response payload. This strict subset rejects any unexpected payload.
    r.finish()
    return result


def sink_transition(current_hud, selection):
    """Controller's observed 0-vs-nonzero branch; not a surface allocator.

    Known profile values are 0 and 1. Other values remain rejected even though
    the machine code branches on zero versus nonzero.
    """
    if type(current_hud) is not bool or type(selection) is not int or selection not in (0, 1):
        raise ValueError('Expected cached boolean and known selection 0/1')
    target_hud = selection == 0
    return {'target': 'hud' if target_hud else 'kombi',
            'switch_required': current_hud != target_hud,
            'scope': 'factory navigation sink state; not an independent surface',
            'drawing_allowed': False}


def decode_packet(packet):
    if not isinstance(packet, bytes) or not 16 <= len(packet) <= MAX_BODY + 16:
        raise ValueError('Invalid SOME/IP packet size')
    service, method, length, client, session, protocol, interface, kind, code = struct.unpack('>HHIHHBBBB', packet[:16])
    if service != 0xb006 or protocol != 1 or interface != 1 or length != len(packet) - 8:
        raise ValueError('Expected one complete B006/interface-1 message')
    result = decode_body(method, kind, code, packet[16:])
    result.update(service=service, client=client, session=session)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('packet', type=Path, help='One saved SOME/IP message, not a PCAP')
    a = p.parse_args()
    try:
        with a.packet.open('rb') as f:
            data = f.read(MAX_BODY + 17)
        print(json.dumps(decode_packet(data), indent=2))
    except (OSError, ValueError) as e:
        p.exit(2, str(e) + '\n')


if __name__ == '__main__':
    main()
