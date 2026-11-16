#!/usr/bin/env python3
"""Validate saved car-test output locally. Never connects to a vehicle."""
import argparse
import json
from pathlib import Path

EXPECTED_TESTS = {'default_suppression', 'rpm_sweep', 'clock_rollback', 'sample_order',
                  'pipeline_and_reply_cadence', 'stale_input', 'overlay_revocation',
                  'ack_timeout', 'monotonic_clock', 'frame_expiry_despite_fresh_input'}

def analyze(text, kind, exit_code):
    if len(text.encode()) > 1024 * 1024:
        raise ValueError('Output exceeds 1 MiB limit')
    records = []
    for line in text.splitlines():
        if line.startswith('{'):
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                raise ValueError('Truncated or malformed JSON record')
    if len(records) != 1 or not isinstance(records[0], dict):
        raise ValueError('Expected exactly one complete JSON summary')
    r = records[0]
    issues = []
    if exit_code != 0:
        issues.append('process_exit_' + str(exit_code))
    evidence = {}
    if kind == 'selftest':
        tests = r.get('tests', [])
        if not isinstance(tests, list) or any(not isinstance(t, dict) for t in tests):
            raise ValueError('Invalid test list')
        if r.get('schema') != 1 or r.get('qnx_target') is not True or r.get('pointer_bits') != 32:
            issues.append('not_verified_QNX_32_bit_target')
        if r.get('vehicle_io') is not False or r.get('pass') is not True:
            issues.append('selftest_failed_or_unexpected_io')
        if len(tests) != len(EXPECTED_TESTS) or any(not isinstance(t.get('name'), str) for t in tests) or {t.get('name') for t in tests} != EXPECTED_TESTS or any(t.get('pass') is not True for t in tests):
            issues.append('missing_duplicate_or_failed_tests')
        evidence['passed_tests'] = sum(t.get('pass') is True for t in tests)
    elif kind in ('registry', 'discovery'):
        if r.get('schema') != 2 or r.get('hud_commands_sent') != 0 or r.get('payloads_captured') is not False:
            issues.append('unexpected_schema_or_transmission')
        for key in ('dropped_snapshots', 'dropped_headers', 'bad_messages'):
            if r.get(key) != 0:
                issues.append(key)
        if r.get('link_state') != 'up':
            issues.append('link_not_up')
        if type(r.get('self_address')) is not int or not 0x2000 <= r['self_address'] <= 0x2fff:
            issues.append('invalid_client_address')
        if type(r.get('elapsed_ms')) is not int or not 14000 <= r['elapsed_ms'] <= 20000:
            issues.append('incomplete_observation_window')
        snapshots = r.get('snapshots', [])
        headers = r.get('headers', [])
        if not isinstance(snapshots, list) or not 1 <= len(snapshots) <= 8:
            raise ValueError('Missing or invalid registry snapshots')
        if not isinstance(headers, list) or len(headers) > 256 or any(not isinstance(h, dict) for h in headers):
            raise ValueError('Invalid bounded header list')
        hosts = set()
        for snapshot in snapshots:
            if not isinstance(snapshot, list) or len(snapshot) > 1024:
                raise ValueError('Invalid registry snapshot')
            matches = []
            for entry in snapshot:
                if not isinstance(entry, dict) or type(entry.get('key')) is not int or type(entry.get('address')) is not int:
                    raise ValueError('Invalid registry entry')
                if entry['key'] == 0x8200:
                    matches.append(entry['address'])
            if kind == 'registry' and (len(matches) != 1 or not 0x100 <= matches[0] <= 0xfff):
                issues.append('HUD_82_00_host_missing_or_ambiguous')
            hosts.update(matches)
        if kind == 'registry' and len(hosts) != 1:
            issues.append('HUD_host_not_unique_across_snapshots')
        evidence = {'hud_hosts': sorted(hosts), 'expected_hud_service_present': len(hosts) == 1, 'snapshot_count': len(snapshots),
                    'hud_header_count': len(headers),
                    'observed_functions': sorted({h.get('function') for h in headers if type(h.get('function')) is int})}
    else:
        raise ValueError('Unknown result kind')
    return {'kind': kind, 'evidence_usable': not issues, 'issues': sorted(set(issues)),
            'evidence': evidence, 'drawing_authorized': False,
            'limits': 'Does not validate ownership, geometry, overlay semantics, acknowledgement matching or cleanup.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('log', type=Path)
    p.add_argument('--kind', choices=['selftest', 'registry', 'discovery'], required=True)
    p.add_argument('--exit-code', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        result = analyze(a.log.read_text(), a.kind, a.exit_code)
    except (ValueError, OSError) as e:
        result = {'kind': a.kind, 'evidence_usable': False, 'issues': [str(e)], 'drawing_authorized': False}
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['evidence_usable'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
