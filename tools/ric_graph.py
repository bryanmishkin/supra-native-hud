"""Offline B006 maneuver graph codecs; no transport or ownership assumptions.

Traced schemas: method 9/tag 2 list state, method 10/tag 1 description.
Unknown variants remain opaque. These are factory navigation messages, not
proof that an independent client or standalone picture can become visible.
"""
import hashlib
import math
import struct
from ric_lifecycle import Reader, MAX_BODY


def _uint(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Expected unsigned integer')
    return value


def _enum(value, maximum):
    _uint(value, 8)
    if value > maximum:
        raise ValueError('Invalid enum')
    return value


def _common(r):
    model_id, model_type = r.u32(), r.take(1)[0]
    _enum(model_type, 50)
    return dict(model_id=model_id, model_type=model_type)


def _ids(r):
    size = r.u32()
    if size % 4:
        raise ValueError('ID array byte extent is not divisible by four')
    raw = r.take(size)
    return list(struct.unpack('>' + 'I' * (size // 4), raw))


def decode_graph_body(method, body):
    if method not in (9, 10):
        raise ValueError('Untraced graph method')
    r = Reader(body)
    handle = r.u32()
    result = _common(r)
    size, tag = r.u32(), r.u32()
    payload = r.take(size)
    r.finish()
    result.update(handle=handle, method=method, variant_tag=tag,
                  payload_bytes=size, payload_sha256=hashlib.sha256(payload).hexdigest(),
                  live_drawing_allowed=False, remote_cleanup_proven=False)
    if tag == 0 and payload:
        raise ValueError('Empty variant has payload')
    if (method, tag) not in ((9, 2), (10, 1)):
        return result
    p = Reader(payload)
    model = _common(p)
    if method == 9:
        model['active_maneuver_id'], model['passive_maneuver_id'] = p.u32(), p.u32()
        model['guidance_state'] = _enum(p.take(1)[0], 8)
        model['expected_arrival_time'], model['total_delay_time'] = struct.unpack('>QQ', p.take(16))
        model['route_length'] = struct.unpack('>d', p.take(8))[0]
        # The primitive accepts all bit patterns. Keep JSON finite and preserve
        # non-finite wire bytes without claiming they are valid route lengths.
        if not math.isfinite(model['route_length']):
            model['route_length_bits'] = payload[30:38].hex()
            model['route_length'] = None
        model['icon_resource_id'] = p.u32()
        key = 'list_state'
    else:
        model['is_passive'] = bool(_enum(p.take(1)[0], 1))
        model['previous_joined'] = bool(_enum(p.take(1)[0], 1))
        model['previous_maneuver_id'] = p.u32()
        model['next_joined'] = bool(_enum(p.take(1)[0], 1))
        model['next_maneuver_id'] = p.u32()
        model['maneuver_direction'] = _enum(p.take(1)[0], 58)
        for name in ('coming_road_id', 'current_state_id', 'detailed_maneuver_id', 'distance_id'):
            model[name] = p.u32()
        for name in ('navigation_event_ids', 'lane_guiding_ids', 'point_of_interest_ids'):
            model[name] = _ids(p)
        key = 'description'
    p.finish()
    model['outer_identity_matches'] = all(model[k] == result[k] for k in ('model_id', 'model_type'))
    result[key] = model
    return result


def decode_graph_packet(packet):
    if not isinstance(packet, bytes) or not 16 <= len(packet) <= MAX_BODY + 16:
        raise ValueError('Invalid packet size')
    svc, method, length, client, session, protocol, interface, kind, code = struct.unpack('>HHIHHBBBB', packet[:16])
    if (svc, protocol, interface, kind, code) != (0xb006, 1, 1, 0, 0) or method not in (9, 10):
        raise ValueError('Expected B006 graph request')
    if length != len(packet) - 8:
        raise ValueError('Invalid packet length')
    result = decode_graph_body(method, packet[16:])
    result.update(client=client, session=session)
    return result


def _body(handle, model_id, model_type, tag, payload):
    if len(payload) > MAX_BODY - 17:
        raise ValueError('Model exceeds decoder bound')
    return struct.pack('>IIBII', _uint(handle), _uint(model_id), _enum(model_type, 50), len(payload), tag) + payload


def encode_list_state_body(handle, model_id, model_type, *, active_maneuver_id,
                           passive_maneuver_id, guidance_state, expected_arrival_time,
                           total_delay_time, route_length, icon_resource_id):
    """Synthetic body builder; caller must specify every field, no live sender."""
    if type(route_length) not in (int, float) or not math.isfinite(route_length):
        raise ValueError('Expected finite route-length value')
    payload = struct.pack('>IBIIBQQdI', _uint(model_id), _enum(model_type, 50),
        _uint(active_maneuver_id), _uint(passive_maneuver_id), _enum(guidance_state, 8),
        _uint(expected_arrival_time, 64), _uint(total_delay_time, 64), route_length, _uint(icon_resource_id))
    return _body(handle, model_id, model_type, 2, payload)


def encode_description_body(handle, model_id, model_type, *, is_passive,
                            previous_joined, previous_maneuver_id, next_joined,
                            next_maneuver_id, maneuver_direction, current_state_id,
                            coming_road_id, detailed_maneuver_id, distance_id,
                            navigation_event_ids, lane_guiding_ids, point_of_interest_ids):
    for b in (is_passive, previous_joined, next_joined):
        if type(b) is not bool:
            raise ValueError('Expected boolean')
    payload = struct.pack('>IBBBIBIBIIII', _uint(model_id), _enum(model_type, 50),
        is_passive, previous_joined, _uint(previous_maneuver_id), next_joined,
        _uint(next_maneuver_id), _enum(maneuver_direction, 58), _uint(coming_road_id),
        _uint(current_state_id), _uint(detailed_maneuver_id), _uint(distance_id))
    for ids in (navigation_event_ids, lane_guiding_ids, point_of_interest_ids):
        if not isinstance(ids, (tuple, list)) or len(ids) > (MAX_BODY - 62) // 4:
            raise ValueError('Expected bounded ID list')
        payload += struct.pack('>I', len(ids) * 4)
        payload += b''.join(struct.pack('>I', _uint(i)) for i in ids)
    return _body(handle, model_id, model_type, 1, payload)


def factory_state_transition_allowed(previous, following):
    """Client filter at 0xaaf350, NOT server policy or an erase guarantee."""
    _enum(previous, 8)
    _enum(following, 8)
    if previous == following:
        return True
    allowed = ({1}, {2, 4, 8, 5}, set(range(2, 9)), {1},
               set(range(2, 9)), {0, 1}, {0}, {2, 4, 8, 5}, set(range(2, 9)))
    return following in allowed[previous]
