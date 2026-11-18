#!/usr/bin/env python3
"""Offline B009 handshake inventory. Never grants readiness or transmits traffic."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from extract_someip_pcap import extract


def decode(packet):
    if len(packet) < 16:
        raise ValueError('short SOME/IP header')
    service, method, length, client, session, pv, iv, kind, rc = struct.unpack('>HHIHHBBBB', packet[:16])
    if length + 8 != len(packet) or (service, pv, iv, rc) != (0xb009, 1, 1, 0):
        raise ValueError('invalid B009 envelope')
    if (method, kind, len(packet)) == (0x8001, 2, 29):
        scale, width, height, selection = struct.unpack('>dHHB', packet[16:])
        if not math.isfinite(scale) or scale <= 0 or not width or not height or selection not in (0, 1):
            raise ValueError('unsupported sink tuple')
        return dict(type='selection', scale=scale, width=width, height=height, selection=selection)
    if (method, kind, len(packet)) == (1, 1, 18):
        selection, status = packet[16:]
        if selection not in (0, 1) or status != 0:
            raise ValueError('unsupported completion')
        return dict(type='completion', selection=selection, status=status)
    raise ValueError('unrecognized B009 message')


def audit(path):
    raw = path.read_bytes()
    parsed = extract(raw, max_packets=65536)
    events, errors = [], []
    for stream in parsed['streams']:
        if stream['parse_error']:
            errors.append(dict(flow=stream['flow'], error=stream['parse_error']))
            continue
        data = stream['data']; offset = 0
        while offset < len(data):
            length = struct.unpack_from('>I', data, offset + 4)[0] + 8
            packet = data[offset:offset + length]
            if packet[:2] == b'\xb0\x09':
                try:
                    row = decode(packet)
                    spans = [s for s in stream['byte_spans'] if s['offset'] <= offset < s['offset'] + s['bytes']]
                    row.update(flow=stream['flow'], offset=offset,
                               timestamp_us=min(s['timestamp_us'] for s in spans))
                    events.append(row)
                except ValueError as e:
                    errors.append(dict(flow=stream['flow'], offset=offset, error=str(e)))
            offset += length
    events.sort(key=lambda x:x['timestamp_us'])
    return dict(pcap_sha256=hashlib.sha256(raw).hexdigest(), packets=parsed['packets'],
                events=events, errors=errors, receiver_binding_proven=False,
                limitation='Captured interval only. No event does not mean no retained factory sink; a factory event is not our producer subscription or physical pixel acceptance.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pcap', type=Path)
    print(json.dumps(audit(p.parse_args().pcap), indent=2))
