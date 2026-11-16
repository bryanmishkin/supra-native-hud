#!/usr/bin/env python3
"""Inspect saved GV shared memory; never opens a device or sends commands.

Without an independently captured event length/sequence, inspect only the first
chunk. The allocation's trailing bytes can contain earlier commands.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

MAX_BYTES = 262144
REUSABLE = 0xfffffffe
# Controller type-name dispatch 0xd43504..0xd43818; GVL 0x76d3ac..0x76d418.
NAMES = {1: 'Header', 2: 'ElementInfo', 0x10001: 'Bargraph',
         0x20001: 'CurrentStreet', 0x20002: 'ComingStreet',
         0x30001: 'DistanceToManeuver', 0x30002: 'DistanceToDestination',
         0x60001: 'Bitmap', 0x70001: 'LGRoundAbout', 0x70002: 'LGBranch',
         0x70003: 'LGIntersection', 0x70004: 'ManeuverHighCCPPicturePosition',
         0x70005: 'ManeuverHighCCP', 0x70006: 'LaneManeuverDescriptor',
         0x70007: 'RoadList', 0x70008: 'HGPictureInPicture',
         0x70009: 'HGIntersectionGeometry', 0x7000a: 'CCPInfo',
         0x7000b: 'CCPLaneInfo', 0x7000c: 'BargraphSegmentation',
         0x7000d: 'ManeuverDistance', 0x7000e: 'ManeuverState',
         0x7000f: 'LaneGuiding', 0x70010: 'ManeuverHighLink',
         0x70011: 'ManeuverHighLinkList', 0x70012: 'ManeuverDescription',
         0x71001: 'GV35Up_RC_Text', 0x71003: 'GV35Up_RC_SvgImage',
         0x71004: 'GV35Up_RC_BitmapImage', 0x80001: 'LabelContainer'}


def inspect(data, event_bytes=None, event_sequence=None):
    if not 20 <= len(data) <= MAX_BYTES:
        raise ValueError('Expected 20..262144 bytes')
    if (event_bytes is None) != (event_sequence is None):
        raise ValueError('Event length and sequence must be supplied together')
    mutex_count, mutex_owner, sequence = struct.unpack_from('<III', data)
    full = event_bytes is not None
    if full:
        if type(event_bytes) is not int or not 20 <= event_bytes <= len(data):
            raise ValueError('Event length exceeds snapshot or is too short')
        if type(event_sequence) is not int or not 0 <= event_sequence <= 0xffffffff:
            raise ValueError('Invalid event sequence')
        if sequence == REUSABLE or event_sequence != sequence:
            raise ValueError('Reusable buffer or mismatched event sequence')
    end = event_bytes if full else len(data)
    chunks = []
    offset = 12
    while offset < end:
        if end - offset < 8:
            raise ValueError('Truncated chunk header')
        kind, size = struct.unpack_from('<II', data, offset)
        if size > end - offset - 8:
            raise ValueError('Chunk extends beyond supplied extent')
        payload = data[offset + 8:offset + 8 + size]
        chunks.append({'offset': offset, 'type': hex(kind),
                       'name': NAMES.get(kind, 'unknown'), 'payload_bytes': size,
                       'payload_sha256': hashlib.sha256(payload).hexdigest()})
        offset += 8 + size
        if not full:
            break
    return {'sha256': hashlib.sha256(data).hexdigest(), 'allocation_bytes': len(data),
            'sequence': sequence, 'reusable': sequence == REUSABLE,
            'mutex_words': [mutex_count, mutex_owner],
            'scope': 'event-bounded' if full else 'first-retained-chunk-only',
            'chunks': chunks, 'uninterpreted_bytes': len(data) - offset,
            'windshield_destination_proven': False,
            'limitation': 'Snapshot is not atomic; event agreement does not prove ownership, destination or an active rendered frame.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('snapshot', type=Path)
    p.add_argument('--event-bytes', type=int)
    p.add_argument('--event-sequence', type=lambda x: int(x, 0))
    a = p.parse_args()
    try:
        with a.snapshot.open('rb') as f:
            data = f.read(MAX_BYTES + 1)
        print(json.dumps(inspect(data, a.event_bytes, a.event_sequence), indent=2))
    except (OSError, ValueError) as e:
        p.exit(2, str(e) + '\n')


if __name__ == '__main__':
    main()
