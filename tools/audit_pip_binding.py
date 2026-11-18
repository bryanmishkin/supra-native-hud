#!/usr/bin/env python3
"""Offline timeline of sink selection and native-image bindings, never a readiness grant."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from extract_someip_pcap import extract
from audit_pip_sink import decode


def binding(packet):
    if len(packet) < 16:
        raise ValueError('short header')
    service, method, length, client, session, pv, iv, kind, rc = struct.unpack('>HHIHHBBBB', packet[:16])
    if length + 8 != len(packet) or pv != 1:
        raise ValueError('invalid envelope')
    if service == 0xb009:
        return decode(packet)
    if service != 0xb006 or iv != 1 or kind != 0 or rc:
        return None
    b = packet[16:]
    # Exact producer shapes used by the retired experiment, not all RIC variants.
    if method == 3 and len(b) == 28:
        handle, rid, typ, size, variant = struct.unpack_from('>IIBII', b)
        inner, inner_type, width, height, depth, packing = struct.unpack_from('>IBHHBB', b, 17)
        if (typ, size, variant, inner_type) == (2, 11, 3, 2):
            if inner != rid or not width or not height:
                raise ValueError('inconsistent native resource')
            return dict(type='native-resource-request', handle=handle, resource=rid,
                        width=width, height=height, depth=depth, packing=packing)
    if method == 11 and len(b) == 71:
        handle, model, typ, size, variant = struct.unpack_from('>IIBII', b)
        inner, inner_type = struct.unpack_from('>IB', b, 17)
        if (typ, size, variant, inner_type) == (7, 54, 6, 7):
            if model != inner:
                raise ValueError('inconsistent detailed model')
            return dict(type='high-guidance-binding-request', handle=handle, model=model,
                        resource=struct.unpack_from('>I', b, 35)[0])
    return None


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
            n = struct.unpack_from('>I', data, offset + 4)[0] + 8
            packet = data[offset:offset+n]
            try:
                row = binding(packet)
                if row:
                    spans = [s for s in stream['byte_spans'] if s['offset'] <= offset < s['offset']+s['bytes']]
                    row.update(flow=stream['flow'], timestamp_us=min(s['timestamp_us'] for s in spans),
                               packet_sha256=hashlib.sha256(packet).hexdigest(),
                               client=struct.unpack_from('>H', packet, 8)[0],
                               session=struct.unpack_from('>H', packet, 10)[0])
                    events.append(row)
            except ValueError as e:
                errors.append(dict(flow=stream['flow'], offset=offset, error=str(e)))
            offset += n
    return dict(pcap_sha256=hashlib.sha256(raw).hexdigest(), events=sorted(events,key=lambda x:x['timestamp_us']),
                errors=errors, receiver_binding_proven=False,
                limitation='Requests and sink events only; no ACK correlation or physical pixel proof. Only exact known native-resource and detail variants decoded. No event does not prove absence of other bindings.')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pcap',type=Path)
    print(json.dumps(audit(p.parse_args().pcap),indent=2))
