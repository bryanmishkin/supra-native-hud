#!/usr/bin/env python3
"""Offline-default, read-only capture of the selected guidance style database."""
import argparse
import json
import re
from pathlib import Path
import capture_runtime as runtime
from consolidated_capture import Session
from capture_output_driver import snapshot, BASELINE, audit

ROOT = '/opt/nav/eceusa/bin'
DIRECTORIES = (ROOT + '/gvStyleDB_ID5_NBTEvo_BMW_USA_1025', ROOT + '/style_config')


def inventory(text, directory):
    paths = text.splitlines()
    if len(paths) > 2048 or len(set(paths)) != len(paths):
        raise ValueError('Oversized or duplicate style inventory')
    for path in paths:
        if not path.startswith(directory + '/') or not re.fullmatch(r'/[A-Za-z0-9_./+-]+', path):
            raise ValueError('Unexpected style path')
        if any(p in ('.', '..', '') for p in path.split('/')[1:]):
            raise ValueError('Noncanonical style path')
    return sorted(paths)


def run(args):
    session = Session(args)
    session.identity()
    expected = json.loads(BASELINE.read_text())['component_sha256']
    before = snapshot(session, 'v1-before', expected)
    if not before['all_15_match']:
        raise ValueError('Baseline mismatch; collection stopped')
    missing = []
    try:
        for directory in DIRECTORIES:
            # No symlink traversal and no devices, pipes, or mapped runtime pseudo-files.
            command = 'find ' + directory + ' -type f -print'
            reply = session.call(command)
            if reply.returncode:
                raise ValueError('Cannot enumerate selected directory: ' + directory)
            paths = inventory(reply.stdout.decode('utf-8'), directory)
            if not paths:
                raise ValueError('Selected directory contains no regular files: ' + directory)
            for path in paths:
                if session.file(path) is None:
                    missing.append(path)
        if session.file(ROOT + '/nav_styles.ini') is None:
            missing.append('nav_styles.ini')
    finally:
        after = snapshot(session, 'v1-after', expected)
        session.report.update(v1_before=before, v1_after=after)
        session.persist()
    if not after['all_15_match']:
        missing.append('V1 baseline mismatch after collection')
    if before['faults'] != after['faults']:
        missing.append('Permanent fault records changed')
    missing.extend(audit(session.root, session.report))
    session.report.update(missing=missing, capture_complete=not missing,
                          drawing_attempted=False, style_decoding_pending=True)
    session.persist()
    return session.report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    for name in ('head', 'local'):
        parser.add_argument('--' + name, type=runtime.link_local)
    for name in ('known-hosts', 'socket', 'output'):
        parser.add_argument('--' + name, type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'network':False,'remote_writes':False,'drawing':False,
            'directories':DIRECTORIES,'configuration':ROOT+'/nav_styles.ini',
            'collection':'Regular files only; double-read verification and local SHA256 manifest',
            'limits':'2048 files/directory, 64 MiB/file, 512 MiB transfer, 20 minutes',
            'preservation':'15 V1 baseline hashes and permanent fault records before/after',
            'purpose':'Resolve selected XAR/XPD view definitions and linked resources; no claim of windshield pixels'},indent=2))
        return 0
    if not all((args.head,args.local,args.known_hosts,args.output)):
        parser.error('Verified addresses, known-hosts and private output directory required')
    report = run(args)
    print(json.dumps({'capture_complete':report['capture_complete'],'missing':report['missing']},indent=2))
    return 0 if report['capture_complete'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
