#!/usr/bin/env python3
"""Experimental bounded PiP graph; offline plan by default. No V1 installation.

This tests a hypothesis, not established windshield routing. The operator must
pause V1 with the existing validation runner and verify stopped guidance first.
The producer command must launch the matching RAM-only thirty-second helper.
"""
import argparse
import hashlib
import json
from pathlib import Path
import select
import socket
import struct
import subprocess
import time

from ric_lifecycle import Reader
from ric_owned_session import OwnedSession
from ric_live_trial import TcpExchange, list_body, ABSENT
from ric_graph import encode_description_body, encode_list_state_body
from ric_guiding import encode_empty_guiding_body


def allocation(packet):
    if len(packet)<24:
        raise ValueError('Missing create response')
    service,method,n,_,_,pv,iv,kind,code=struct.unpack('>HHIHHBBBB',packet[:16])
    if (service,method,n,pv,iv,kind,code)!=(0xb006,1,len(packet)-8,1,1,128,0):
        raise ValueError('Wrong create response envelope')
    r=Reader(packet[16:]); handle=r.u32(); entries=Reader(r.take(r.u32()));r.finish()
    models={}; pip=None
    while entries.pos<len(entries.data):
        size,tag=entries.u32(),entries.u32(); raw=entries.take(size)
        if tag==35:
            if pip is not None or len(raw)!=16:raise ValueError('Ambiguous PiP configuration')
            pip=struct.unpack('>BBIIHHBB',raw)
        if tag in (19,17,20,21,4,1,18) and len(raw)>=10:
            k,t,count,offset=struct.unpack_from('>BBII',raw)
            if (tag,t) in ((19,7),(17,15),(20,32),(21,33),(4,17),(1,34),(18,29)):
                if t in models or not count or offset+count>0xffffffff:raise ValueError('Bad model allocation')
                models[t]=offset+count-1
    # Exact retained Supra contract; not a configurable universal installer.
    if handle!=200 or pip!=(35,2,5,0x02000000,320,320,1,0):
        raise ValueError('Not the retained Supra PiP profile')
    expected={7:0x07000004,15:0x0f000004,32:0x20000000,33:0x21000000,
              17:0x11000000,34:0x22000004,29:0x1d00001d}
    if models!=expected:raise ValueError('Unexpected model allocation: '+repr(models))
    return dict(handle=handle,resource_id=0x02000004,models=models,
                width=320,height=200,depth=0,packing=0,
                supported_depth=pip[6],supported_packing=pip[7])


def measured_support(raw,a):
    if hashlib.sha256(raw).hexdigest()!='f621e800338a3225f9fecf20f98b6938034aafb4f6bebb208e1ea156b89f4791':
        raise ValueError('Expected exact accepted V1 support profile')
    if raw[:8]!=b'SHP1\0\x0a\0\x07':raise ValueError('Bad support profile')
    rows=[];i=8
    while i<len(raw):
        method,n=struct.unpack_from('>HI',raw,i);i+=6
        body=raw[i:i+n];i+=n
        if len(body)!=n:raise ValueError('Truncated support profile')
        rows.append((method,body))
    if len(rows)!=17:raise ValueError('Unexpected profile count')
    selected=[rows[1],rows[2],rows[9],rows[16]]
    for (method,body),(m,t) in zip(selected,[(10,34),(10,29),(9,17),(9,17)]):
        if method!=m or len(body)<9 or body[8]!=t or struct.unpack_from('>II',body)!=(200,a['models'][t]):
            raise ValueError('Support field identity mismatch')
    # The existing V1 road icon does not need the close-maneuver stage. Its
    # saved distance is 461 m but GS3 threshold is only 92 m. PiP detailed
    # guidance does need that stage: mirror ryseek's explicit 1000 m test
    # threshold in a working copy, never in the installed profile.
    current=bytearray(selected[0][1])
    if len(current)!=59 or struct.unpack_from('>I',current,13)[0]!=5:
        raise ValueError('Unexpected current-state descriptor')
    struct.pack_into('>d',current,38,1000.0)
    a['support_start']=[(10,bytes(current).hex()),(selected[1][0],selected[1][1].hex())]
    a['position_start']=selected[2][1].hex();a['position_stop']=selected[3][1].hex()
    return a


def producer_contract(a):
    # Resource capability maxima are not a producer's selected format.
    return dict(schema=2, description_id=a['models'][15], resource_id=a['resource_id'],
                backing=[800,480], content=[a['width'],a['height']],
                depth=a['depth'], packing=a['packing'], screen_format=8,
                metadata_id_be=struct.pack('>I',a['models'][15]).hex())


def validate_producer(output,a):
    rows=[line[len(b'PIP_BINDING '):] for line in output.splitlines()
          if line.startswith(b'PIP_BINDING ')]
    if len(rows)!=1 or json.loads(rows[0])!=producer_contract(a):
        raise ValueError('Local producer/descriptor contract mismatch')


def descriptor(a):
    rid=a['resource_id']
    payload=struct.pack('>IBHHBB',rid,2,a['width'],a['height'],a['depth'],a['packing'])
    return struct.pack('>IIBII',200,rid,2,len(payload),3)+payload


def detail(a):
    # ryseek's graph_template phase_b_27: detailed model type 7, variant 6.
    # Fixed 54-byte member; high-guidance resource is body offset 35.
    # Only explicit model/resource identities differ from that reference shape.
    p=bytearray(54)
    struct.pack_into('>IB',p,0,a['models'][7],7);p[5]=1
    struct.pack_into('>I',p,18,a['resource_id'])
    struct.pack_into('>I',p,50,ABSENT)
    return struct.pack('>IIBII',200,a['models'][7],7,54,6)+p


def state(a,value,active=ABSENT):
    return encode_list_state_body(200,a['models'][33],33,
        active_maneuver_id=active,passive_maneuver_id=ABSENT,guidance_state=value,
        expected_arrival_time=0x80000000,total_delay_time=0,
        route_length=-float.fromhex('0x1.fffffffffffffp+1023'),icon_resource_id=ABSENT)


def steps(a):
    d=encode_description_body(200,a['models'][15],15,is_passive=False,
        previous_joined=False,previous_maneuver_id=ABSENT,next_joined=False,
        next_maneuver_id=ABSENT,maneuver_direction=7,current_state_id=a['models'][34],
        coming_road_id=ABSENT,detailed_maneuver_id=a['models'][7],distance_id=a['models'][29],
        navigation_event_ids=[],lane_guiding_ids=[],point_of_interest_ids=[])
    return [(9,state(a,1))]+[(m,bytes.fromhex(b)) for m,b in a['support_start']]+[(11,bytes(detail(a))),(10,d),
            (12,list_body(200,a['models'][32],a['models'][15])),
            (4,struct.pack('>I',200)),(9,state(a,2,a['models'][15])),(9,bytes.fromhex(a['position_start']))]


def withdrawal(a):
    return [(9,state(a,5)),(9,state(a,0)),(12,list_body(200,a['models'][32])),
            (11,encode_empty_guiding_body(200,a['models'][7],7)),
            (4,struct.pack('>I',200)),(9,bytes.fromhex(a['position_stop']))]


class Session(OwnedSession):
    def __init__(self,exchange,a):
        super().__init__(exchange,('SupraHUD.PiPTrial','SupraHUD.Test','bryanmishkin'),(3,3,1),0x5350)
        self.handle=200;self.state='created';self.a=a

    def _request(self,method,body):
        if len(body)<4 or struct.unpack_from('>I',body)[0]!=200:raise ValueError('Wrong instance')
        if method not in (2,3,4,8,9,10,11,12):raise ValueError('Forbidden operation')
        if method in (2,3,8) and (len(body)<8 or struct.unpack_from('>I',body,4)[0]!=self.a['resource_id']):
            raise ValueError('Outside selected PiP slot')
        if method in (9,10,11,12):
            if len(body)<9 or self.a['models'].get(body[8])!=struct.unpack_from('>I',body,4)[0]:
                raise ValueError('Outside selected models')
        return super()._request(method,body)


def run(s,a,producer,record,stop_producer=None):
    result=dict(status='preflight',uploaded=False,graph_attempted=False,
                local_cleanup=False,resource_absent=None,cleanup=[],visual_pass=False)
    attempted=False; child=None; output=b''
    def save():result['journal']=s.journal;record(result)
    try:
        if s._check(a['resource_id'],2):raise ValueError('PiP slot occupied; no overwrite')
        attempted=True;save()
        s._empty(3,descriptor(a)); result['uploaded']=True;save()
        if not s._check(a['resource_id'],2):raise ValueError('PiP configuration not present')
        child=subprocess.Popen(producer,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+3
        while b'PRODUCER_READY\n' not in output:
            if time.monotonic()>=deadline:raise TimeoutError('No native first-post confirmation')
            if select.select([child.stdout],[],[],.05)[0]:
                chunk=child.stdout.read1(4096)
                if not chunk:raise RuntimeError('Producer exited before first post')
                output+=chunk
                if len(output)>65536:raise RuntimeError('Excess producer output')
        validate_producer(output,a)
        result['producer_contract_verified']=True
        result['receiver_binding_verified']=False
        result['graph_attempted']=True;save()
        s.timeout=.5
        for m,b in steps(a):
            if child.poll() is not None:raise RuntimeError('Producer ended before graph activation')
            s._empty(m,b);save()
        result['status']='marker_window';save()
        print('MARKER TEST RUNNING: watch windshield and cluster; producer runs for 30 seconds total.',flush=True)
        tail,_=child.communicate(timeout=35);output+=tail
        result['local_cleanup']=child.returncode==0 and b'local_cleanup=1' in output
        if not result['local_cleanup']:raise RuntimeError('Native producer cleanup not confirmed')
        result['status']='finished'
    except (Exception,KeyboardInterrupt) as e:
        result['status']='failed';result['error']=str(e) or type(e).__name__
    finally:
        s.timeout=1
        # Stop pixels first, then references, then only our attempted resource.
        if child is not None and child.poll() is None:
            if stop_producer:
                try:
                    stop=subprocess.run(stop_producer,capture_output=True,timeout=5)
                    result['stop_request_exit']=stop.returncode
                except Exception as e:result['stop_request_error']=str(e)
            else:child.terminate() # Host test subprocess, not a remote kill claim.
            try:
                tail,_=child.communicate(timeout=35 if stop_producer else 3);output+=tail
                result['local_cleanup']=child.returncode==0 and b'local_cleanup=1' in output
            except subprocess.TimeoutExpired:
                child.kill();child.communicate();result['local_cleanup']=False
        if child is not None and child.stdout is not None:child.stdout.close()
        result['producer_output']=output.decode('utf-8','replace')[-65536:]
        if result['graph_attempted']:
            for m,b in withdrawal(a):
                row={'method':m,'ack':False};result['cleanup'].append(row)
                try:s._empty(m,b);row['ack']=True
                except Exception as e:row['error']=str(e)
                save()
        if attempted:
            row={'method':8,'ack':False};result['cleanup'].append(row)
            try:s._empty(8,struct.pack('>II',200,a['resource_id']));row['ack']=True
            except Exception as e:row['error']=str(e)
            try:result['resource_absent']=not s._check(a['resource_id'],2)
            except Exception as e:result['absence_error']=str(e)
        result['protocol_cleanup']=attempted and result['resource_absent'] is True and all(x['ack'] for x in result['cleanup'])
        result['resume_v1_allowed']=False # Explicit owner visual check and normal restart are separate.
        save()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--create-response',type=Path,required=True)
    p.add_argument('--support-profile',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--v1-paused-and-displays-clear',action='store_true')
    p.add_argument('--guidance-stopped',action='store_true')
    p.add_argument('--local-port',type=int)
    p.add_argument('--producer-argv',type=Path,help='Reviewed JSON argv for matching RAM helper; no shell')
    p.add_argument('--producer-stop-argv',type=Path,help='Reviewed argv to create its private RAM stop file')
    args=p.parse_args()
    if args.execute:
        p.error('Live PiP runner retired after two failed image tests: receiver sink binding is unverified. Offline plans remain available.')
    raw=args.create_response.read_bytes();a=measured_support(args.support_profile.read_bytes(),allocation(raw))
    args.output.mkdir(parents=True,exist_ok=False)
    plan=dict(allocation=a,create_sha256=hashlib.sha256(raw).hexdigest(),
        configure=descriptor(a).hex(),steps=[(m,b.hex()) for m,b in steps(a)],
        withdrawal=[(m,b.hex()) for m,b in withdrawal(a)],
        producer_description_id=a['models'][15],producer_contract=producer_contract(a),live_verified=False,
        hypothesis='Native 800x480 secondary backing -> 320x200 PiP -> detailed maneuver; destination must be observed')
    (args.output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    if not args.execute:print('Offline plan saved; no connection or drawing.');return
    if not (args.v1_paused_and_displays_clear and args.guidance_stopped and args.producer_argv and args.producer_stop_argv and args.local_port and 1<=args.local_port<=65535):
        p.error('Explicit parked admission, producer argv and verified local forward required')
    producer=json.loads(args.producer_argv.read_text())
    if not isinstance(producer,list) or not producer or any(not isinstance(v,str) or not v or '\0' in v for v in producer):p.error('Invalid producer argv')
    stop=json.loads(args.producer_stop_argv.read_text())
    if not isinstance(stop,list) or not stop or any(not isinstance(v,str) or not v or '\0' in v for v in stop):p.error('Invalid producer stop argv')
    def record(result):
        tmp=args.output/'result.tmp';tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(args.output/'result.json')
    with socket.create_connection(('127.0.0.1',args.local_port),2) as sock:
        s=Session(TcpExchange(sock,args.output),a);r=run(s,a,producer,record,stop)
    if not (r['status']=='finished' and r['local_cleanup'] and r['protocol_cleanup']):raise SystemExit(1)

if __name__=='__main__':main()
