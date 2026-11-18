#!/usr/bin/env python3
"""Offline codec for the NavigationFully PiP metadata upload block.

This is the 84-byte CPU-side imageSubData input, NOT a SOME/IP payload or
proof of the final framebuffer channel order. No network or drawing operations.
"""
import argparse
import json
from pathlib import Path

SIZE = 84
WIDTH = 21
HEIGHT = 1


def _check(data):
    if len(data) != SIZE:
        raise ValueError('PiP metadata block must be exactly 84 bytes')


def encode_record(record):
    """Convert opaque 84-byte metadata to traced CPU-side pixel bytes."""
    _check(record)
    return b''.join(record[i+1:i+4] + record[i:i+1] for i in range(0, SIZE, 4))


def decode_upload(upload):
    """Undo per-word byte rotation; does not detect metadata in arbitrary pixels."""
    _check(upload)
    return b''.join(upload[i+3:i+4] + upload[i:i+3] for i in range(0, SIZE, 4))


def describe_upload(upload):
    record = decode_upload(upload)
    return {
        'cpu_upload_size': SIZE, 'image_width': WIDTH, 'image_height': HEIGHT,
        'record_hex': record.hex(),
        # NavigationFully 0x7ee598 / 0x7f6464 stores maneuver+0x200 here.
        'ric_maneuver_id_little_endian': int.from_bytes(record[16:20], 'little'),
        'source_identity_or_framebuffer_order_verified': False,
        'larger_windshield_test_ready': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upload', type=Path, help='exact 84-byte CPU upload block')
    args = parser.parse_args()
    print(json.dumps(describe_upload(args.upload.read_bytes()), indent=2))
