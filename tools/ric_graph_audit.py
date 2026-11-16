#!/usr/bin/env python3
"""Inspect image-reference chains in one saved, ordered SOME/IP stream.

Never joins different streams/handles and never connects to a vehicle. Reports
partial factory graph evidence, not proof of an independently visible surface.
"""
import argparse
import json
import struct
from pathlib import Path
from ric_graph import decode_graph_packet
from ric_guiding import decode_guiding_packet
from ric_resource import decode_resource_packet
from ric_lifecycle import MAX_BODY, decode_packet as decode_lifecycle_packet


def audit_stream(data):
    if not isinstance(data, bytes) or len(data) > 32 * 1024 * 1024:
        raise ValueError('Expected stream bytes up to 32 MiB')
    models, resources, states = {}, {}, {}
    result = {'messages': 0, 'events': [], 'live_drawing_allowed': False,
              'remote_cleanup_proven': False}

    def chain(client, handle, state):
        active = state['active_maneuver_id']
        view = dict(active_maneuver_id=active, guidance_state=state['guidance_state'])
        if active == 0xffffffff:
            view['status'] = 'no active maneuver reference'
            return view
        description = models.get((client, handle, active), {}).get('description')
        if not description:
            view['status'] = 'description missing or untraced'
            return view
        detail_id = description['detailed_maneuver_id']
        view['detailed_maneuver_id'] = detail_id
        detail = models.get((client, handle, detail_id), {})
        picture = detail.get('high_roundabout')
        if not picture:
            view['status'] = 'detail is absent or is not the traced picture variant'
            view['detail_variant_tag'] = detail.get('variant_tag')
            return view
        resource_id = picture['picture_resource_id']
        view['picture_resource_id'] = resource_id
        bitmap = resources.get((client, handle, resource_id), {}).get('bitmap')
        view['status'] = 'bitmap reference chain present' if bitmap else 'bitmap missing or untraced'
        # Even a complete chain lacks the negotiated policy and full enclosing
        # graph. Never label this result as a visible or executable test.
        return view

    offset = 0
    while offset < len(data):
        if len(data) - offset < 16:
            raise ValueError('Truncated SOME/IP header')
        service, method, length, client, session, protocol, interface, kind, code = struct.unpack_from('>HHIHHBBBB', data, offset)
        end = offset + length + 8
        if length < 8 or length > MAX_BODY + 8 or end > len(data):
            raise ValueError('Invalid SOME/IP extent')
        result['messages'] += 1
        if service == 0xb006 and kind == 0 and method in (4, 7, 8):
            lifecycle = decode_lifecycle_packet(data[offset:end])
            handle = lifecycle['handle']
            # Invalidate cached evidence on lifecycle requests; this is NOT
            # an assertion that a request succeeded or an image disappeared.
            if method in (4, 7):
                for cache in (models, resources, states):
                    for key in list(cache):
                        if key[:2] == (client, handle):
                            del cache[key]
            else:
                resources.pop((client, handle, lifecycle['resource_id']), None)
            result['events'].append(dict(offset=offset, method=method, client=client,
                handle=handle, status='lifecycle request; cached evidence invalidated',
                remote_cleanup_proven=False))
        if service == 0xb006 and kind == 0 and method in (3, 9, 10, 11):
            decoder = decode_resource_packet if method == 3 else decode_guiding_packet if method == 11 else decode_graph_packet
            record = decoder(data[offset:end])
            handle = record['handle']
            for key in ('description', 'list_state', 'high_roundabout', 'bitmap'):
                if key in record and not record[key]['outer_identity_matches']:
                    raise ValueError('Mismatched inner model/resource identity')
            if method == 3:
                resources[(client, handle, record['resource_id'])] = record
            else:
                models[(client, handle, record['model_id'])] = record
                if 'list_state' in record:
                    states[(client, handle, record['model_id'])] = record['list_state']
            for (c, h, model_id), state in states.items():
                if (c, h) == (client, handle):
                    result['events'].append(dict(offset=offset, method=method, client=c,
                        handle=h, state_model_id=model_id, **chain(c, h, state)))
        offset = end
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stream', type=Path)
    args = parser.parse_args()
    try:
        with args.stream.open('rb') as f:
            data = f.read(32 * 1024 * 1024 + 1)
        print(json.dumps(audit_stream(data), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, str(error)+'\n')

if __name__ == '__main__':
    main()
