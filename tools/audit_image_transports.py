#!/usr/bin/env python3
"""Compare captured B006 image uploads offline; never infer visibility from ACKs."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from extract_someip_pcap import extract
from inspect_someip_stream import inspect
from ric_resource import decode_resource_packet


def audit(path):
    raw = path.read_bytes()
    result = {'capture': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
              'uploads': [], 'excluded_streams': [], 'prefixes': []}
    for stream in extract(raw, max_bytes=64*1024*1024, max_packets=65536)['streams']:
        data = stream['data']
        if stream['parse_error']:
            match = re.fullmatch(r'truncated (?:body|header) at offset (\d+)', stream['parse_error'])
            if not match:
                result['excluded_streams'].append({'flow': stream['flow'], 'reason': stream['parse_error']})
                continue
            data = data[:int(match[1])]
            result['prefixes'].append({'flow': stream['flow'], 'bytes': len(data)})
        inspect(data)
        offset = 0
        while offset < len(data):
            size = int.from_bytes(data[offset+4:offset+8], 'big') + 8
            packet = data[offset:offset+size]
            if packet[:4] == bytes.fromhex('b0060003') and packet[14] == 0:
                row = decode_resource_packet(packet)
                row.update(offset=offset, flow=stream['flow'])
                result['uploads'].append(row)
            offset += size
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    seen, captures, excluded = set(), [], []
    for path in sorted(args.root.rglob('*.pcap')):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            captures.append(audit(path))
        except (ValueError, OSError) as error:
            excluded.append({'capture': str(path), 'reason': str(error)})
    groups = {}
    for capture in captures:
        for row in capture['uploads']:
            detail = row.get('bitmap', row.get('picture_in_picture', {}))
            key = (row['client'], row['resource_type'], row['variant_tag'], tuple(detail.get('resolution_pair', [])))
            label = repr(key)
            group = groups.setdefault(label, {'client': row['client'], 'resource_type': row['resource_type'],
                'variant_tag': row['variant_tag'], 'resolution': list(key[3]), 'count': 0,
                'inline_image_bytes': 0, 'resource_ids': []})
            group['count'] += 1
            group['inline_image_bytes'] += detail.get('image_bytes', 0)
            if row['resource_id'] not in group['resource_ids']:
                group['resource_ids'].append(row['resource_id'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'groups': list(groups.values()), 'captures': captures,
        'excluded_captures': excluded, 'unique_capture_hashes': len(seen),
        'limitation': 'Counts may overlap across independent recordings of the same event. No ACK, model-reference, visibility or receiver-pixel attachment inference.'}, indent=2)+'\n')
    print(json.dumps({'groups': list(groups.values()), 'unique_captures': len(seen), 'excluded': len(excluded)}, indent=2))

if __name__ == '__main__':
    main()
