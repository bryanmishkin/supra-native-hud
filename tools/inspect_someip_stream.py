#!/usr/bin/env python3
"""Offline header inventory of one reassembled, gap-free TCP direction.

Input must begin at a SOME/IP message boundary; not a PCAP or raw packet dump.
Never connects, transmits, resynchronizes, or treats metadata as drawing permission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MAX_STREAM = 16 * 1024 * 1024
MAX_MESSAGE = 1024 * 1024
MAX_MESSAGES = 65536


def inspect(data):
    if len(data) > MAX_STREAM:
        raise ValueError('stream exceeds 16 MiB')
    rows = {}
    offset = count = 0
    while offset < len(data):
        if count >= MAX_MESSAGES:
            raise ValueError('message limit exceeded')
        if len(data) - offset < 16:
            raise ValueError('truncated header at offset %d' % offset)
        service, method, length, client, session, protocol, interface, kind, result = struct.unpack_from('>HHIHHBBBB', data, offset)
        size = 8 + length
        if length < 8 or size > MAX_MESSAGE:
            raise ValueError('invalid message length at offset %d' % offset)
        if size > len(data) - offset:
            raise ValueError('truncated body at offset %d' % offset)
        if protocol != 1:
            raise ValueError('unsupported protocol at offset %d' % offset)
        key = (service, method, interface, kind, result)
        row = rows.setdefault(key, dict(service=service, method=method, interface=interface,
                                      message_type=kind, return_code=result, count=0,
                                      min_body_bytes=size-16, max_body_bytes=size-16))
        row['count'] += 1
        row['min_body_bytes'] = min(row['min_body_bytes'], size-16)
        row['max_body_bytes'] = max(row['max_body_bytes'], size-16)
        offset += size
        count += 1
    return dict(schema=1, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                messages=count, headers=[rows[k] for k in sorted(rows)],
                live_drawing_authorized=False,
                limitation='Header inventory only; no ECU identity, ownership, display destination or drawing semantics proven.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stream', type=Path)
    args = parser.parse_args()
    try:
        with args.stream.open('rb') as f:
            data = f.read(MAX_STREAM + 1)
        print(json.dumps(inspect(data), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
