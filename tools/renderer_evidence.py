#!/usr/bin/env python3
"""Offline renderer signature inventory. Hits are leads, never compatibility proof.

Reads regular files supplied explicitly; does not extract archives, load code,
connect to a service, or infer a protocol from a numeric service ID alone.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_BYTES = 128 * 1024 * 1024
PATTERNS = {
    'ric_client': rb'CSomeIPRICServiceGuidanceClientBase',
    'ric_server_lead': rb'RICServiceGuidance(?:SomeIP)?(?:Stub|Server)|RbRicService',
    'ric_interface': rb'BMW\.INFOTAINMENT\.REMOTEINSTRUMENTCLUSTER\.RICServiceGuidance',
    'dcsm2_interface': rb'de\.bmw\.infotainment\.dcsm\.Dcsm2',
    'dcsm2_watchdog': rb'DCSM2 WATCHDOG TIMEOUT',
    'ramses_library': rb'libramses[^\x00\s/]{0,80}',
    'ramses_api': rb'RamsesFramework|RamsesClient|ramses::',
}


def inspect(data):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError('Expected at most 128 MiB of bytes')
    hits = {}
    for name, pattern in PATTERNS.items():
        count, offsets = 0, []
        for match in re.finditer(pattern, data):
            count += 1
            if len(offsets) < 32:
                offsets.append(match.start())
        if count:
            hits[name] = {'count': count, 'offsets': offsets}
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'elf': data.startswith(b'\x7fELF'), 'signatures': hits,
            'server_implementation_proven': False,
            'negative_search_excludes_stripped_or_compressed_code': False,
            'live_drawing_allowed': False}


def inspect_file(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular non-symlink file')
    with path.open('rb') as f:
        data = f.read(MAX_BYTES + 1)
    result = inspect(data)
    result['path'] = str(path)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('files', nargs='+', type=Path)
    a = p.parse_args()
    try:
        print(json.dumps([inspect_file(f) for f in a.files], indent=2))
    except (OSError, ValueError) as e:
        p.exit(2, str(e) + '\n')


if __name__ == '__main__':
    main()
