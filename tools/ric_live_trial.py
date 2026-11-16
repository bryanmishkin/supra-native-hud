#!/usr/bin/env python3
"""Bounded experimental own-session picture trial. No connection without --live.

This tests a candidate minimal navigation-picture graph, not a proven arbitrary
HUD surface. A protocol ACK is never a visual pass. Uses only create-returned
allocation offsets; never replays a factory graph or modifies coding/firmware.
"""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import select
import signal
import socket
import struct
import sys
import time
import zlib

from ric_lifecycle import MAX_BODY, Reader, decode_bitmap_config
from ric_owned_session import OwnedSession, RicFailure
from ric_graph import encode_description_body, encode_list_state_body
from ric_guiding import encode_high_roundabout_body

ABSENT = 0xffffffff
# Distinct application identity; protocol version is the factory-observed tuple.
IDENTITY = ('SupraHUD.MarkerTrial', 'SupraHUD.OwnSession', 'bryanmishkin')
VERSIONS = (3, 3, 1)
SERVER_COOKIE = bytes.fromhex('ffff800000000008deadbeef01018000')


def choose_allocation(body):
    """Select one bitmap and four models from returned configuration only.

    a35194 -> a66478 constructs available IDs as offset + index (no type shift).
    a35440 selects type 10 for the high-roundabout container. Config variants
    have common kind/type/count/offset prefix; unknown tails remain unconsumed.
    This is a candidate contract, not evidence of exclusive server ownership.
    """
    r = Reader(body)
    handle, size = r.u32(), r.u32()
    a = Reader(r.take(size)); r.finish()
    models, bitmap = {}, []
    required = {10: (1,), 15: (17,), 32: (20,), 33: (21,)}
    variants = []
    while a.pos < len(a.data):
        if len(variants) >= 256:
            raise RicFailure('Too many configurations')
        n, tag = a.u32(), a.u32()
        raw = a.take(n)
        variants.append(dict(tag=tag, hex=raw.hex()))
        if tag == 33:
            b = decode_bitmap_config(raw)
            if b['formats']['png'] and b['resource_element_count']:
                bitmap.append(b)
        elif tag in (1, 17, 20, 21):
            if len(raw) < 10:
                raise RicFailure('Truncated model configuration')
            kind, typ, count, offset = struct.unpack_from('>BBII', raw)
            if kind > 39 or typ > 50:
                raise RicFailure('Invalid model configuration')
            if typ in required and tag in required[typ]:
                if typ in models:
                    raise RicFailure('Ambiguous duplicate model configuration')
                if count == 0 or offset == ABSENT or count > ABSENT-offset:
                    raise RicFailure('Missing or overflowing model allocation')
                models[typ] = offset
    if set(models) != set(required):
        raise RicFailure('Own session does not advertise required picture/description/list/state models')
    if len(set(models.values())) != len(models):
        raise RicFailure('Overlapping model allocations')
    if len(bitmap) != 1:
        raise RicFailure('Expected exactly one PNG bitmap configuration')
    b = bitmap[0]
    w, h = b['resolution_pair']
    if not (8 <= w <= 512 and 8 <= h <= 512):
        raise RicFailure('Unsupported advertised bitmap dimensions')
    off, count = b['resource_element_offset'], b['resource_element_count']
    if off == ABSENT or count > ABSENT-off:
        raise RicFailure('Invalid resource allocation')
    return dict(handle=handle, models=models, resource_id=off,
                resource_type=b['resource_type'], dimensions=[w, h], variants=variants)


def marker_png(width, height):
    """Lossless RGB black field with distinctive white box and central cross."""
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data)&ABSENT)
    rows = []
    for y in range(height):
        row = bytearray(b'\0')
        for x in range(width):
            lit = ((x in (2, width-3) and 2 <= y <= height-3) or
                   (y in (2, height-3) and 2 <= x <= width-3) or
                   (abs(x-width//2) <= 1 and height//4 <= y <= 3*height//4) or
                   (abs(y-height//2) <= 1 and width//4 <= x <= 3*width//4))
            row.extend(b'\xff\xff\xff' if lit else b'\0\0\0')
        rows.append(row)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+
            chunk(b'IDAT',zlib.compress(b''.join(rows),9))+chunk(b'IEND',b''))


class TcpExchange:
    """Persistent TCP, bounded framing and deadline; no reconnect/retransmission."""
    def __init__(self, sock, directory):
        self.sock, self.directory, self.sequence = sock, Path(directory), 0
        self.broken = False

    def __call__(self, packet, timeout):
        if self.broken:
            raise RicFailure('Transport failed earlier; no reconnect or blind retry')
        self.sequence += 1
        stem = '%03d' % self.sequence
        self._save(stem+'-request.bin', packet)
        deadline = time.monotonic()+timeout
        def remaining():
            left = deadline-time.monotonic()
            if left <= 0:
                raise TimeoutError('Exchange deadline exceeded')
            self.sock.settimeout(left)
        def read(n):
            chunks = bytearray()
            while len(chunks) < n:
                remaining()
                data = self.sock.recv(n-len(chunks))
                if not data:
                    raise EOFError('Connection closed before complete response')
                chunks.extend(data)
            return bytes(chunks)
        try:
            remaining(); self.sock.sendall(packet)
            for cookie in range(5):
                header = read(16)
                if header == SERVER_COOKIE:
                    self._save(stem+'-cookie-%d.bin' % cookie, header)
                    continue
                n = struct.unpack_from('>I',header,4)[0]
                if not 8 <= n <= MAX_BODY+8:
                    raise RicFailure('Response length outside bounds')
                result = header+read(n-8)
                self._save(stem+'-response.bin',result)
                return result
            raise RicFailure('Too many magic cookies')
        except BaseException:
            # Partial reads cannot safely be treated as a new frame next time.
            self.broken = True
            raise

    def _save(self, name, data):
        with (self.directory/name).open('xb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())


def list_body(handle, model_id, description_id=None):
    # Method12/tag1: common prefix, active from/count/total u16 + byte array;
    # passive from/count/total u16 + byte array. Verified against saved 46B body.
    n = int(description_id is not None)
    payload = struct.pack('>IBHHHI', model_id,32,0,n,n,4*n)
    if n:
        payload += struct.pack('>I',description_id)
    payload += struct.pack('>HHHI',0,0,0,0)
    return struct.pack('>IIBII',handle,model_id,32,len(payload),1)+payload


class DrawingTrial:
    def __init__(self, session, record, observe, begin_cleanup=lambda: None):
        self.session, self.record, self.observe = session, record, observe
        self.begin_cleanup = begin_cleanup
        self.allocation = None
        self.graph_started = False
        self.result = dict(status='not_started', visual_test_passed=False,
                           own_session_accepted=False, windshield_marker_seen=None,
                           marker_removed=None, factory_normal=None, cleanup_steps=[])

    def save(self):
        self.result['journal'] = self.session.journal
        self.record(self.result)

    def send(self, method, body):
        self.session._active()
        self.session._empty(method,body)
        self.save()

    def state(self, state, active=ABSENT):
        a = self.allocation
        return encode_list_state_body(self.session.handle,a['models'][33],33,
            active_maneuver_id=active,passive_maneuver_id=ABSENT,guidance_state=state,
            expected_arrival_time=0x80000000,total_delay_time=0,
            route_length=-sys.float_info.max,icon_resource_id=ABSENT)

    def withdraw(self):
        if not self.graph_started:
            return
        # Every cleanup action attempted independently, even after a rejected ACK.
        a, h = self.allocation, self.session.handle
        actions = [(9,self.state(5)), (9,self.state(0)),
                   (12,list_body(h,a['models'][32])),
                   (11,encode_high_roundabout_body(h,a['models'][10],10,0,2,ABSENT)),
                   (4,struct.pack('>I',h))]
        for method, body in actions:
            step = dict(method=method,acknowledged=False)
            self.result['cleanup_steps'].append(step)
            try:
                self.session._empty(method,body)
                step['acknowledged'] = True
            except Exception as e:
                step['error'] = str(e)
            self.save()

    def run(self):
        try:
            self.result['status'] = 'creating'; self.save()
            self.session.open()
            self.result['own_session_accepted'] = True
            # Persist the raw configuration even when selection rejects it.
            self.result['create_response_hex'] = self.session.configuration_body.hex()
            self.save()
            self.allocation = choose_allocation(self.session.configuration_body)
            self.result['allocation'] = self.allocation
            self.result['status'] = 'uploading'; self.save()
            a, h = self.allocation, self.session.handle
            png = marker_png(*a['dimensions'])
            self.result['marker_sha256'] = hashlib.sha256(png).hexdigest()
            self.session.upload_bitmap(a['resource_id'],a['resource_type'],a['dimensions'],png)
            self.result['status'] = 'graph_attempt'; self.graph_started = True; self.save()
            self.send(9,self.state(1))
            self.send(11,encode_high_roundabout_body(h,a['models'][10],10,0,2,a['resource_id']))
            self.send(10,encode_description_body(h,a['models'][15],15,
                is_passive=False,previous_joined=False,previous_maneuver_id=ABSENT,
                next_joined=False,next_maneuver_id=ABSENT,maneuver_direction=8,
                current_state_id=ABSENT,coming_road_id=ABSENT,
                detailed_maneuver_id=a['models'][10],distance_id=ABSENT,
                navigation_event_ids=[],lane_guiding_ids=[],point_of_interest_ids=[]))
            self.send(12,list_body(h,a['models'][32],a['models'][15]))
            self.send(4,struct.pack('>I',h))
            self.send(9,self.state(2,a['models'][15]))
            self.result['status'] = 'observing_marker'; self.save()
            self.result['windshield_marker_seen'] = self.observe('marker',15)
        except (Exception, KeyboardInterrupt) as e:
            self.result['status'] = 'failed_or_interrupted'
            self.result['error'] = str(e) or type(e).__name__
        finally:
            self.begin_cleanup()
            try:
                self.withdraw()
            finally:
                self.result['cleanup'] = self.session.close()
                self.save()
        # Observation is after disposal and never holds resources indefinitely.
        if self.graph_started:
            self.result['marker_removed'] = self.observe('removed',20)
            self.result['factory_normal'] = self.observe('factory',20)
        cleanup = self.result['cleanup']
        cleanup_ok = (cleanup['instance_dispose_acknowledged'] and
            all(x['acknowledged'] for x in self.result['cleanup_steps']) and
            all(x['dispose_acknowledged'] and x['post_dispose_check'] is False
                for x in cleanup['resources']))
        self.result['visual_test_passed'] = bool(cleanup_ok and
            self.result['windshield_marker_seen'] is True and
            self.result['marker_removed'] is True and self.result['factory_normal'] is True)
        if self.result['status'] != 'failed_or_interrupted':
            self.result['status'] = 'passed' if self.result['visual_test_passed'] else 'inconclusive'
        self.save()
        return self.result


def observation(which, seconds):
    prompts = {'marker':'Is OUR white box/cross visible in the WINDSHIELD (not just the cluster)?',
               'removed':'Is our marker now GONE from the windshield?',
               'factory':'Do factory HUD, iDrive, radio selector and navigation respond normally?'}
    print(prompts[which]+' Type yes/no within %d seconds; no answer means unknown.' % seconds,flush=True)
    deadline = time.monotonic()+seconds
    while time.monotonic() < deadline:
        if select.select([sys.stdin],[],[],max(0,deadline-time.monotonic()))[0]:
            value = sys.stdin.readline()
            if not value:
                return None
            if value.strip().lower() in ('yes','no'):
                return value.strip().lower() == 'yes'
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live',action='store_true')
    p.add_argument('--host',help='Numeric IPv4 endpoint or already-established local SSH tunnel')
    p.add_argument('--port',type=int,default=30502)
    p.add_argument('--output',type=Path,required=True,help='New evidence directory; must not exist')
    p.add_argument('--client-id',type=lambda x:int(x,0),default=0x5348)
    args = p.parse_args()
    if not 1 <= args.client_id <= 65535 or not 1 <= args.port <= 65535:
        p.error('Client ID and port must be nonzero u16')
    if args.live and (not args.host or ipaddress.ip_address(args.host).version != 4):
        p.error('--live requires a numeric IPv4 --host')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'marker-preview.png').write_bytes(marker_png(128,64))
    def record(data):
        tmp = args.output/'result.tmp'
        with tmp.open('w') as f:
            json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        tmp.replace(args.output/'result.json')
    if not args.live:
        record(dict(status='prepared_no_network',identity=IDENTITY,versions=VERSIONS,
                    runtime_verified=False,visual_test_passed=False))
        print('Offline preparation only. No connection made. See LIVE-DRAWING-TEST.md.')
        return 0
    # First SIGINT/SIGTERM enters finally; subsequent signals cannot interrupt cleanup.
    def stop(signum, frame):
        signal.signal(signal.SIGINT,signal.SIG_IGN)
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        raise KeyboardInterrupt('Stop requested; attempting cleanup')
    signal.signal(signal.SIGINT,stop); signal.signal(signal.SIGTERM,stop)
    sock = None
    try:
        sock = socket.create_connection((args.host,args.port),timeout=2)
        transport = TcpExchange(sock,args.output)
        session = OwnedSession(transport,IDENTITY,VERSIONS,args.client_id,timeout=2)
        def begin_cleanup():
            signal.signal(signal.SIGINT,signal.SIG_IGN)
            signal.signal(signal.SIGTERM,signal.SIG_IGN)
        result = DrawingTrial(session,record,observation,begin_cleanup).run()
        print(json.dumps({k:result.get(k) for k in ('status','own_session_accepted','visual_test_passed','error')},indent=2))
        return 0 if result['visual_test_passed'] else 2
    except (Exception,KeyboardInterrupt) as e:
        # Do not overwrite a trial journal if observation was interrupted.
        if not (args.output/'result.json').exists():
            record(dict(status='connection_failed',error=str(e),visual_test_passed=False))
        print(str(e),file=sys.stderr)
        return 2
    finally:
        if sock is not None:
            sock.close()


if __name__ == '__main__':
    sys.exit(main())
