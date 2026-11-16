#!/usr/bin/env python3
"""Package audited candidates locally. No SSH, upload, activation or car execution."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

CANDIDATES = ('supra-hud-selftest-qnx', 'supra-hud-offline-replay-qnx', 'supra-registry-observer-qnx')

def prepare(build, audits, output):
    checked = []
    for name in CANDIDATES:
        binary = build / name
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        audit = json.loads((audits / (name + '.audit.json')).read_text())
        if audit.get('static_gate_passed') is not True or audit.get('candidate', {}).get('sha256') != digest:
            raise ValueError('Missing, failed or stale static audit: ' + name)
        checked.append({'file': name, 'sha256': digest, 'bytes': binary.stat().st_size})
    output.mkdir(parents=True, exist_ok=False)
    for entry in checked:
        shutil.copy2(build / entry['file'], output / entry['file'])
    (output / 'manifest.json').write_text(json.dumps({'schema': 1, 'files': checked,
        'car_tested': False, 'drawing_enabled': False, 'persistent_install': False}, indent=2)+'\n')
    # Deliberately separate tests; the default package never launches the private DSI adapter.
    for file, binary, option in [('run-selftest.sh', CANDIDATES[0], '--self-test'),
                                  ('run-replay.sh', CANDIDATES[1], '--simulate'),
                                  ('run-observer.sh', CANDIDATES[2], '--observe-registry')]:
        script = output / file
        script.write_text('#!/bin/sh\nset -eu\ncase "$0" in */*) cd "${0%/*}" ;; esac\n'
            'case "$(uname -s):$(uname -n):$(uname -p)" in\n'
            '  QNX:hu-omap:armle*) ;;\n'
            '  *) echo "Stopped: expected direct QNX hu-omap ARM target" >&2; exit 65 ;;\n'
            'esac\n' + ('export LD_LIBRARY_PATH=/opt/sys/lib:/boot/lib:/lib\n' if binary == CANDIDATES[2] else '') + 'exec ./' + binary + ' ' + option + '\n')
        script.chmod(0o755)
    (output / 'RESULTS.json').write_text(json.dumps({'schema': 1, 'vehicle': '2026 GR Supra manual / NBTevo_T24081I',
        'tests': {name: {'status': 'not_run', 'exit_code': None, 'log': None}
          for name in ('identity_and_hashes', 'selftest', 'offline_replay', 'registry_baseline',
                       'registry_radio_overlay', 'registry_navigation_overlay', 'cleanup')},
        'drawing_profile': 'unverified', 'persistent_startup': 'not_installed'}, indent=2)+'\n')
    return checked

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--audits', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    try:
        print(json.dumps(prepare(a.build,a.audits,a.output),indent=2))
    except (OSError,ValueError,KeyError) as e:
        p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
