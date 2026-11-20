#!/usr/bin/env python3
"""Bounded A102 HUD surface experiment. Default is offline plan only.
No installation, session change, unlocking, coding, reset or arbitrary requests.
"""
import argparse
import datetime
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import time
from capture_receiver_identity import exact
from verify_current_v1_test_baseline import verify as verify_v1

ECU=0x60
STOP=bytes.fromhex('3102a102')
CASES={'rgb':bytes.fromhex('3101a10200102030'), 'grid':bytes.fromhex('3101a1025c000000')}
IDENTITY_HASHES={'22f197':'9dc9443dd68d889b70cab73b6713e1a5e244525e1df41fc2e08ba7bac4830809','22f101':'4406c00b629b281dba5556e98dee448fafbf368a51e8556f99063efb03259af4'}
ALLOWED={STOP,*CASES.values(),*(bytes.fromhex(k) for k in IDENTITY_HASHES)}

class Exchange:
    def __init__(self,gateway,source,interface,journal):
        self.gateway,self.source,self.interface,self.journal=gateway,source,interface,journal
    def __call__(self,req):
        if req not in ALLOWED:raise ValueError('Request is outside fixed test allowlist')
        self.journal('request',request=req.hex())
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            if self.interface:
                if sys.platform!='darwin':raise ValueError('Interface binding requires macOS')
                sock.setsockopt(socket.IPPROTO_IP,25,socket.if_nametoindex(self.interface))
            sock.bind((self.source,0));sock.connect((self.gateway,6801))
            sock.sendall(struct.pack('>IHBB',len(req)+2,1,0xf4,ECU)+req)
            deadline=time.monotonic()+5
            for _ in range(64):
                length,kind=struct.unpack('>IH',exact(sock,6,deadline))
                if not 0<=length<=65536:raise ValueError('Oversized HSFZ frame')
                payload=exact(sock,length,deadline)
                self.journal('frame',kind=kind,payload=payload.hex())
                if kind==0x12:
                    sock.sendall(struct.pack('>IHBB',2,0x13,0,0xf4));continue
                if kind!=1 or payload[:2]!=bytes([ECU,0xf4]):continue
                reply=payload[2:]
                if reply==bytes([0x7f,req[0],0x78]):continue
                if reply[:2]==bytes([0x7f,req[0]]):return reply
                prefix=bytes([req[0]+0x40])+req[1:3] if req[0]==0x22 else bytes([0x71])+req[1:4]
                if reply.startswith(prefix):return reply
            raise TimeoutError('Response frame limit exceeded')

def positive(exchange,request):
    reply=exchange(request)
    expected=b'\x71'+request[1:4]
    if reply!=expected:raise RuntimeError('Unexpected routine response: '+reply.hex())
    return reply

def cleanup(exchange,journal):
    for attempt in range(1,4):
        try:
            positive(exchange,STOP);journal('cleanup_ack',attempt=attempt)
            return True
        except Exception as e:journal('cleanup_failure',attempt=attempt,error=str(e))
    return False

def trial(exchange,case,journal,watch=time.sleep):
    # Successful inverse command is required before any activation on installed 008.
    positive(exchange,STOP);journal('preflight_stop_ack')
    clean=False
    try:
        # Cleanup is armed BEFORE sending start, including a lost start reply.
        positive(exchange,CASES[case]);journal('start_ack',case=case)
        print('WATCH NOW: '+case+' — 30 seconds',flush=True)
        journal('viewing_window',seconds=30);watch(30)
    finally:
        old={s:signal.signal(s,signal.SIG_IGN) for s in (signal.SIGINT,signal.SIGTERM)}
        try:clean=cleanup(exchange,journal)
        finally:
            for s,h in old.items():signal.signal(s,h)
        journal('trial_end',cleanup_acknowledged=clean,visual_cleanup_verified=False)
        if not clean:raise RuntimeError('STOP NOT ACKNOWLEDGED. Keep connection and ignition stable; use cleanup-only. No next test.')
    return clean

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--case',choices=CASES)
    p.add_argument('--cleanup-only',action='store_true')
    p.add_argument('--gateway');p.add_argument('--source-ip');p.add_argument('--interface')
    p.add_argument('--output',type=Path);p.add_argument('--v1-pre',type=Path)
    p.add_argument('--ssh-socket',type=Path);p.add_argument('--head')
    p.add_argument('--stationary-v1-paused',action='store_true',help='Operator confirms parked, stable ignition, V1 cooperatively paused and both displays normal')
    a=p.parse_args()
    plan=dict(ecu='60',routine='A102',cases={k:v.hex() for k,v in CASES.items()},stop=STOP.hex(),seconds=30,
        offline_firmware='004.000.003',installed_firmware='008.000.000',compatibility='Unverified routine behavior on 008; require exact receiver identity and stop ACK before start',
        scope='Full test surface activation and height, not uploaded-image access',default_network=False,
        cleanup='Three bounded stop attempts; requires stable operating state; no ECU-side expiry proven',v1_files_modified=False)
    if not a.execute:print(json.dumps(plan,indent=2));return
    if not all([a.gateway,a.source_ip,a.output]):p.error('Explicit gateway, source IP and new output directory required')
    ipaddress.IPv4Address(a.gateway);ipaddress.IPv4Address(a.source_ip)
    if not a.cleanup_only and (not a.case or not a.v1_pre or not a.stationary_v1_paused or not a.ssh_socket or not a.head):p.error('Choose case; supply current V1 capture, verified SSH master/head and stationary/paused confirmation')
    if a.cleanup_only and a.case:p.error('Cleanup-only cannot include a start case')
    baseline=None if a.cleanup_only else verify_v1(a.v1_pre)
    if not a.cleanup_only:
        ipaddress.IPv4Address(a.head)
        command="grep -q '^STOPPED$' /tmp/supra-hud-v1/resident.status && test ! -e /tmp/supra-hud-v1/factory.sock && test ! -e /tmp/supra-hud-v1/active.jsonl.handoff"
        checked=subprocess.run(['ssh','-S',str(a.ssh_socket.resolve()),'-o','BatchMode=yes','-o','ConnectTimeout=3','root@'+a.head,command],capture_output=True,timeout=5)
        if checked.returncode:raise RuntimeError('V1 is not confirmed stopped; no diagnostic test permitted')
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    if baseline:(a.output/'v1-preverified.json').write_text(json.dumps(baseline,indent=2)+'\n')
    with (a.output/'journal.jsonl').open('a') as log:
        def journal(event,**kw):
            log.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),event=event,**kw))+'\n');log.flush();os.fsync(log.fileno())
        exchange=Exchange(a.gateway,a.source_ip,a.interface,journal)
        def interrupt(signum,frame):raise KeyboardInterrupt('Interrupted; stopping HUD test')
        signal.signal(signal.SIGTERM,interrupt)
        try:
            if a.cleanup_only:
                if not cleanup(exchange,journal):raise RuntimeError('Cleanup not acknowledged')
            else:
                for req,digest in IDENTITY_HASHES.items():
                    reply=exchange(bytes.fromhex(req))
                    if hashlib.sha256(reply).hexdigest()!=digest:raise RuntimeError('Receiver identity mismatch: '+req)
                journal('identity_matched',firmware='008.000.000',routine_compatibility_proven=False)
                trial(exchange,a.case,journal)
            print('STOP acknowledged. Visually confirm pattern gone and factory displays normal before next test or unplugging. V1 remains paused.',flush=True)
        except BaseException as e:
            journal('error',error=str(e));raise

if __name__=='__main__':main()
