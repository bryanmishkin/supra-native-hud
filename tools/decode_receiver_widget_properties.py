#!/usr/bin/env python3
"""Decode widget properties from private, decompressed Candera scene payloads.

No vehicle access or firmware modification. Pointer fields retain the 12-byte
record header origin although the supplied payload excludes that header.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def decode(scene, names):
    def word(offset):
        return struct.unpack_from('<I', scene, offset)[0]

    def string(pointer, start, end):
        offset = pointer - 12
        if not start <= offset <= end - 2:
            raise ValueError('property string pointer outside widget')
        length = struct.unpack_from('<H', scene, offset)[0]
        if not length or offset + 2 + length > end:
            raise ValueError('property string length outside widget')
        raw = scene[offset + 2:offset + 2 + length]
        if raw[-1:] != b'\0':
            raise ValueError('property string lacks terminator')
        return raw[:-1].decode('utf-8')

    widgets = []
    for offset in range(0, len(scene) - 31, 4):
        if word(offset + 4) != 0xa01:
            continue
        size, _, name_key, class_key = struct.unpack_from('<IIII', scene, offset)
        if name_key not in names or class_key not in names:
            continue
        count = word(offset + 24)
        end = offset + size
        if size < 28 + count * 8 or end > len(scene):
            raise ValueError(f'invalid widget extent at {offset:#x}')
        properties = {}
        for i in range(count):
            entry = offset + 28 + i * 8
            key, pointer = struct.unpack_from('<II', scene, entry)
            if key not in names or names[key] in properties:
                raise ValueError(f'unknown or duplicate property at {entry:#x}')
            properties[names[key]] = {
                'value': string(pointer, offset + 28 + count * 8, end),
                'entry_offset': hex(entry),
                'string_offset': hex(pointer - 12),
            }
        widgets.append({'offset': hex(offset), 'size': size,
                        'name': names[name_key], 'class': names[class_key],
                        'properties': properties})
    return widgets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', required=True, type=Path)
    parser.add_argument('--string-index', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    scene = args.scene.read_bytes()
    index = args.string_index.read_bytes()
    names = {int(row['offset'], 16) - 0x220: row['text']
             for row in json.loads(index)}
    widgets = decode(scene, names)
    if not widgets:
        raise ValueError('no widget records decoded')
    result = {'scene_sha256': hashlib.sha256(scene).hexdigest(),
              'string_index_sha256': hashlib.sha256(index).hexdigest(),
              'scope': 'Serialized scene properties, not installed runtime state',
              'widgets': widgets}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Decoded {len(widgets)} widgets; saved {args.output}')


if __name__ == '__main__':
    main()
