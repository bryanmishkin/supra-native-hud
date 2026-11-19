#!/usr/bin/env python3
"""Offline PiP existence transactions, paired only on exact reversed TCP flows.
No sockets. A positive resource check establishes existence, not visible pixels.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from extract_someip_pcap import extract
from inspect_someip_stream import inspect
from ric_resource_check import decode_check_packet


def audit_streams(streams):
    requests, replies, prefixes, rejected = {}, {}, [], []
    for stream in streams:
        data = stream['data']
        flow = tuple(stream['flow'])
        error = stream.get('parse_error')
        if error:
            match = re.fullmatch(r'truncated (?:body|header) at offset (\d+)', error)
            if not match:
                rejected.append({'flow': flow, 'error': error})
                continue
            data = data[:int(match[1])]
            prefixes.append({'flow': flow, 'bytes': len(data), 'error': error})
        inspect(data)  # No guessed resynchronization, even for recovered prefixes.
        offset = 0
        while offset < len(data):
            size = int.from_bytes(data[offset+4:offset+8], 'big') + 8
            packet = data[offset:offset+size]
            start = offset
            offset += size
            if packet[:4] != bytes.fromhex('b0060002'):
                continue
            decoded = decode_check_packet(packet)
            row = {'offset': start, 'flow': flow, **decoded}
            keyflow = flow if decoded['message_type'] == 0 else (flow[2], flow[3], flow[0], flow[1])
            key = (keyflow, decoded['client'], decoded['session'])
            target = requests if decoded['message_type'] == 0 else replies
            target.setdefault(key, []).append(row)
    transactions = []
    for key, rows in requests.items():
        for row in rows:
            if row['resource_type'] != 2:
                continue
            responses = replies.get(key, [])
            transactions.append({'request': row, 'responses': responses,
                                 'unambiguous': len(rows) == len(responses) == 1})
    return {'transactions': transactions, 'recovered_prefixes': prefixes,
            'rejected_streams': rejected, 'visible_pixels_proven': False,
            'limitation': 'Existence only; repeated transaction keys remain ambiguous; no stream resynchronization.'}


def audit(path):
    data = path.read_bytes()
    result = audit_streams(extract(data, max_bytes=64*1024*1024, max_packets=65536)['streams'])
    return {'capture': str(path), 'sha256': hashlib.sha256(data).hexdigest(), **result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path, nargs='+')
    args = parser.parse_args()
    results = []
    for path in args.captures:
        try:
            results.append(audit(path))
        except (ValueError, OSError) as error:
            results.append({'capture': str(path), 'excluded_reason': str(error)})
    print(json.dumps(results, indent=2))
