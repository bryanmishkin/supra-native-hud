#!/usr/bin/env python3
"""Corrected native HUD-profile experiment. Offline plans by default; no V1 writes.

Distinct from the retired G30-template runner. Physical binding is experimental.
"""
import argparse,hashlib,json,select,socket,struct,subprocess,time
from pathlib import Path
from pip_trial import allocation,measured_support,descriptor,steps,withdrawal,Session
from ric_live_trial import TcpExchange
from b006_distance import replace_distance
from verify_current_v1_test_baseline import verify as verify_v1


def plan(create,profile,style,distance=461):
    if style not in ('day','night'):raise ValueError('Explicit owned day/night profile required')
    a=measured_support(profile,allocation(create))
    if distance not in (461,69):raise ValueError('Only measured-distance control and below-fourth-threshold contrast allowed')
    method,body=a['support_start'][1]
    if method!=10:raise ValueError('Expected distance support model')
    a['support_start'][1]=(method,replace_distance(bytes.fromhex(body),distance).hex())
    a.update(width=277,height=160,guidance_type=8402,style=style,distance=distance)
    return a


def producer_contract(a):
    return dict(schema=4 if a.get("allow_hud_candidate") else 3,description_id=a['models'][15],resource_id=a['resource_id'],
        backing=[800,480],content=[277,160],depth=0,packing=0,screen_format=8,
        metadata_id_be=struct.pack('>I',a['models'][15]).hex(),guidance_type=8402,
        style=a['style'],destination_flag=0,selection=1)


def validate_producer(output,a):
    rows=[x[len(b'PIP_BINDING '):] for x in output.splitlines() if x.startswith(b'PIP_BINDING ')]
    if len(rows)!=1:raise ValueError("Expected one producer contract")
    observed=json.loads(rows[0]);expected=producer_contract(a)
    if a.get("allow_hud_candidate") and observed.get("selection") in (0,1):
        expected["selection"]=observed["selection"]
    if observed!=expected:
        raise ValueError('Corrected producer contract mismatch')
    confirmation=b'SINK_NEGOTIATED_HUD_CANDIDATE\n' if observed['selection']==0 else b'SINK_NEGOTIATED_CLUSTER\n'
    if confirmation not in output:
        raise ValueError('No owned sink negotiation confirmation')


def argv(path):
    value=json.loads(path.read_text())
    if not isinstance(value,list) or not value or any(not isinstance(x,str) or not x or '\0' in x for x in value):
        raise ValueError('Expected reviewed nonempty argv array')
    return value

def run(s,a,producer,record,go_producer,stop_producer):
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
        deadline=time.monotonic()+12
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
        subprocess.run(go_producer,check=True,capture_output=True,timeout=3)
        deadline=time.monotonic()+3
        while b'VISIBLE_WINDOW_STARTED\n' not in output:
            if time.monotonic()>=deadline:raise TimeoutError('Visible window start not confirmed')
            if select.select([child.stdout],[],[],.05)[0]:
                chunk=child.stdout.read1(4096)
                if not chunk:raise RuntimeError('Producer ended before visible window')
                output+=chunk
                if len(output)>65536:raise RuntimeError('Excess producer output')
        result['status']='marker_window';save()
        print('WATCH NOW: corrected HUD-profile marker, 30 seconds; inspect windshield AND cluster.',flush=True)
        tail,_=child.communicate(timeout=35);output+=tail
        result['local_cleanup']=b'local_cleanup=1' in output and b'unsubscribe_sent=1' in output
        if not result['local_cleanup']:raise RuntimeError('Native producer cleanup not confirmed')
        if child.returncode!=0 or b'full_visible_window=1' not in output:raise RuntimeError('Full 30-second window did not complete')
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
                result['local_cleanup']=b'local_cleanup=1' in output and b'unsubscribe_sent=1' in output
            except subprocess.TimeoutExpired:
                child.kill();child.communicate();result['local_cleanup']=False
        if child is not None and child.stdout is not None:child.stdout.close()
        # An early admission failure may still report clean native teardown.
        ends=[line for line in output.splitlines() if line.startswith(b'PRODUCER_END ')]
        if len(ends)==1:
            fields=dict(x.split(b'=',1) for x in ends[0].split()[1:] if b'=' in x)
            result['local_cleanup']=fields.get(b'local_cleanup')==b'1' and fields.get(b'unsubscribe_sent')==b'1'
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
    p.add_argument('--style',choices=['day','night'],required=True)
    p.add_argument('--distance',type=int,choices=[461,69],default=461,help='Controlled receiver-stage experiment; not a proven HUD selection trigger')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--observe-hud-selection',action='store_true',help='Experimental received HUD tuple support; does not request or guarantee HUD destination')
    p.add_argument('--v1-pre',type=Path)
    p.add_argument('--v1-paused-and-displays-clear',action='store_true')
    p.add_argument('--guidance-stopped',action='store_true')
    p.add_argument('--local-port',type=int)
    p.add_argument('--producer-argv',type=Path)
    p.add_argument('--go-argv',type=Path)
    p.add_argument('--stop-argv',type=Path)
    args=p.parse_args()
    a=plan(args.create_response.read_bytes(),args.support_profile.read_bytes(),args.style,args.distance)
    a['allow_hud_candidate']=args.observe_hud_selection
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'plan.json').write_text(json.dumps(dict(allocation=a,producer_contract=producer_contract(a),
        descriptor=descriptor(a).hex(),steps=[(m,b.hex()) for m,b in steps(a)],
        withdrawal=[(m,b.hex()) for m,b in withdrawal(a)],physical_binding_verified=False,
        v1_modified=False,visible_seconds=30),indent=2))
    if not args.execute:print('Corrected candidate plan saved; no vehicle connection.');return 0
    if not (args.v1_pre and args.v1_paused_and_displays_clear and args.guidance_stopped and
        args.producer_argv and args.go_argv and args.stop_argv and args.local_port and 1<=args.local_port<=65535):
        p.error('Explicit parked admission, current V1 capture, owned forwarding and reviewed helper commands required')
    (args.output/'v1-preverified.json').write_text(json.dumps(verify_v1(args.v1_pre),indent=2))
    producer,go,stop=argv(args.producer_argv),argv(args.go_argv),argv(args.stop_argv)
    def record(result):
        tmp=args.output/'result.tmp';tmp.write_text(json.dumps(result,indent=2));tmp.replace(args.output/'result.json')
    with socket.create_connection(('127.0.0.1',args.local_port),2) as sock:
        s=Session(TcpExchange(sock,args.output),a);r=run(s,a,producer,record,go,stop)
    return 0 if r['status']=='finished' and r['local_cleanup'] and r['protocol_cleanup'] else 2
if __name__=='__main__':raise SystemExit(main())
