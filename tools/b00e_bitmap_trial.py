#!/usr/bin/env python3
"""Bounded shared-widget content experiment. Offline by default; never modifies V1.

Requires a current-session factory Carousel snapshot to restore. A generated
bitmap or protocol acknowledgment alone does not establish windshield display.
"""
import argparse,hashlib,json,signal,socket,struct,time
from pathlib import Path
from b00e_carousel import decode,encode,replace_selected_content
import b00e_entertainment as entertainment
from b00e_resource_lifecycle import check_body,check_reply,dispose_resource_body
from ric_resource import encode_bitmap_body
from ric_rle32 import encode_bgra,decode_bgra
from ric_live_trial import TcpExchange

# Full retained create-body hash. Exact profile gate, not a claim of ownership.
CONFIG_SHA='21ff4431fc9c2360bcac942688513004f8b1063a5cf19e30b334b5eb4e82d398'
HANDLE=100
RID=0x01000009
ABSENT=0xffffffff

def focus(mid):
    payload=struct.pack('>IBI',0x65,0x2e,mid)
    return struct.pack('>IIBII',HANDLE,0x65,0x2e,len(payload),3)+payload

def prepare_binding(restore,content_field=1,row=None,column=None):
    if len(restore)<9:raise ValueError('Short model snapshot')
    typ=restore[8]
    if typ==0x1c:
        if row is not None or column is not None:raise ValueError('Carousel does not use table coordinates')
        original=decode(restore)
        if any(RID in item for item in original['elements']):raise ValueError('Restoration snapshot references the test slot')
        candidate=replace_selected_content(restore,RID,content_field)
        return candidate,0x6d,dict(content_field=content_field)
    if typ==0x16:
        original=entertainment.decode(restore)
        refs=[original['header_reference']]+original['trailing_references']+[cell[0] for item in original['rows'] for cell in item]
        if RID in refs:raise ValueError('Restoration snapshot references the test slot')
        candidate=entertainment.replace_content_cell(restore,RID,row,column)
        return candidate,0x66,dict(row=row,column=column)
    raise ValueError('Only traced Carousel and Entertainment models supported')

class Trial:
    def __init__(self,exchange,restore,record,observe,content_field=1,row=None,column=None):
        self.candidate,self.model_id,binding=prepare_binding(restore,content_field,row,column)
        self.exchange,self.restore,self.record,self.observe=exchange,restore,record,observe
        self.seq=0;self.uploaded=False;self.model_attempted=False;self.cleaning=False
        self.result=dict(journal=[],cleanup=[],visual_pass=False,shared_factory_session=True,
                         exclusive_ownership=False,status='prepared',
                         binding='captured-content-cell',model_id=self.model_id,cell=binding,
                         candidate_body_sha256=hashlib.sha256(self.candidate).hexdigest())
    def req(self,method,body,empty=True):
        self.seq+=1
        if method not in (2,3,4,8,9,11):raise ValueError('Forbidden method')
        if body[:4]!=struct.pack('>I',100):raise ValueError('Wrong handle')
        p=struct.pack('>HHIHHBBBB',0xb00e,method,len(body)+8,0x5349,self.seq,1,1,0,0)+body
        row=dict(method=method,sequence=self.seq,body_sha256=hashlib.sha256(body).hexdigest(),outcome='uncertain')
        self.result['journal'].append(row);self.record(self.result)
        reply=self.exchange(p,2.0)
        if not isinstance(reply,bytes) or len(reply)<16:raise ValueError('Short reply')
        hdr=struct.unpack('>HHIHHBBBB',reply[:16])
        if hdr!=(0xb00e,method,len(reply)-8,0x5349,self.seq,1,1,0x80,0):raise ValueError('Uncorrelated/failed reply')
        if empty and reply[16:]:raise ValueError('Nonempty acknowledgment')
        row['outcome']='acknowledged';self.record(self.result);return reply[16:]
    def present(self,rid):return check_reply(self.req(2,check_body(100,rid,1),False))
    def step(self,label,fn):
        row=dict(step=label,ok=False);self.result['cleanup'].append(row)
        try:fn();row['ok']=True
        except Exception as e:row['error']=str(e)
        self.record(self.result);return row['ok']
    def run(self,raw,width,height):
        if (width,height) not in ((36,36),(64,64),(96,96),(128,128)):raise ValueError('Unsupported bounded candidate')
        if len(raw)!=width*height*4 or any(a!=255 for a in raw[3::4]):raise ValueError('Expected opaque BGRA')
        image=encode_bgra(raw)
        if decode_bgra(image,width*height)!=raw:raise ValueError('Encoding mismatch')
        self.result['pixel_sha256']=hashlib.sha256(raw).hexdigest()
        self.result['bitmap_dimensions']=[width,height]
        try:
            # Conservative initial admission. No write if any advertised slot is in use.
            states={hex(r):self.present(r) for r in range(0x01000000,0x0100000a)}
            self.result['initial_pool']=states
            if any(states.values()):raise ValueError('Factory bitmap pool in use; no write')
            if self.present(RID):raise ValueError('Candidate slot changed before upload')
            self.uploaded=True # Intent before send: lost ACK may still mean allocated.
            self.req(3,encode_bitmap_body(100,RID,1,[width,height],image))
            if not self.present(RID):raise ValueError('Upload not present')
            # Preserve the factory model; replace only one traced bitmap-capable cell.
            candidate=self.candidate
            self.model_attempted=True
            self.req(11,candidate);self.req(9,focus(self.model_id));self.req(4,struct.pack('>I',100))
            self.result['status']='observing';self.record(self.result)
            self.observe(self) # 30s; read-only resource checks keep transport drained.
            self.result['status']='window_finished'
        except (Exception,KeyboardInterrupt) as e:
            self.result['status']='failed_or_interrupted';self.result['error']=str(e) or type(e).__name__
        finally:
            self.cleaning=True
            detached=True
            if self.model_attempted:
                # Restore full captured factory model before deleting our image.
                for label,m,b in [('withdraw focus',9,focus(ABSENT)),('commit withdrawal',4,struct.pack('>I',100)),
                                  ('restore exact factory model',11,self.restore),('commit restore',4,struct.pack('>I',100))]:
                    ok=self.step(label,lambda m=m,b=b:self.req(m,b));detached=ok and detached
            if self.uploaded and detached:
                self.step('dispose only test bitmap',lambda:self.req(8,dispose_resource_body(100,RID)))
                def absent():
                    if self.present(RID):raise ValueError('Bitmap still present')
                self.step('verify test bitmap absent',absent)
            elif self.uploaded:
                self.result['retained_bitmap_due_to_uncertain_detachment']=True
            self.result['protocol_cleanup_ok']=bool(self.uploaded and self.result['cleanup'] and all(s['ok'] for s in self.result['cleanup']))
            self.record(self.result)
        return self.result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--port',type=int)
    p.add_argument('--admission',type=Path);p.add_argument('--bitmap-bgra',type=Path)
    p.add_argument('--size',type=int,choices=[36,64,96,128]);p.add_argument('--output',type=Path)
    p.add_argument('--content-field',type=int,choices=[1,2],default=1)
    p.add_argument('--row',type=int,help='Entertainment transmitted-array row, explicit')
    p.add_argument('--column',type=int,help='Entertainment existing content column, explicit; never icon column 0')
    a=p.parse_args()
    if not a.execute:
        print('Offline: B00E Carousel/Entertainment content test; 30s; restore current factory snapshot; dispose/check only test bitmap. Requires fresh admission; no connection made.');return
    if not all([a.port,a.admission,a.bitmap_bgra,a.size,a.output]):p.error('All live arguments are required')
    if not 1<=a.port<=65535:p.error('Invalid loopback forward port')
    admission=json.loads(a.admission.read_text())
    if not 0<=time.time()-admission['verified_at_unix']<=120:raise ValueError('Admission must be current (120s)')
    required=['parked','v1_paused_cleanly','v1_hashes_match','factory_overlays_closed','focus_is_absent','same_session_snapshot','exclusive_operator_window','manual_recovery_verified']
    if any(admission.get(k) is not True for k in required):raise ValueError('Missing verified admission condition')
    config=bytes.fromhex(admission['configuration_body_hex'])
    if hashlib.sha256(config).hexdigest()!=CONFIG_SHA:raise ValueError('Unrecognized B00E profile')
    restore=bytes.fromhex(admission.get('restore_model_body_hex') or admission['restore_carousel_body_hex'])
    candidate,model_id,_=prepare_binding(restore,a.content_field,a.row,a.column)
    raw=a.bitmap_bgra.read_bytes()
    if len(raw)!=a.size*a.size*4 or any(v!=255 for v in raw[3::4]):raise ValueError('Invalid opaque marker')
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'admission.json').write_text(json.dumps(admission,indent=2))
    (a.output/'restore-model.bin').write_bytes(restore)
    (a.output/'candidate-model.bin').write_bytes(candidate)
    def record(r):
        t=a.output/'result.tmp';t.write_text(json.dumps(r,indent=2));t.replace(a.output/'result.json')
    def observe(t):
        print('WATCH NOW: 30-second IU/cross marker window. Distinguish windshield from cluster.',flush=True)
        end=time.monotonic()+30
        while time.monotonic()<end:
            time.sleep(min(1,max(0,end-time.monotonic())))
            if not t.present(RID):raise ValueError('Test bitmap disappeared during window')
    active=[]
    def cancel(*_):
        if active and active[0].cleaning:return
        raise KeyboardInterrupt('Operator cancellation')
    signal.signal(signal.SIGTERM,cancel);signal.signal(signal.SIGINT,cancel)
    with socket.create_connection(('127.0.0.1',a.port),timeout=2) as sock:
        trial=Trial(TcpExchange(sock,a.output),restore,record,observe,a.content_field,a.row,a.column);active.append(trial)
        r=trial.run(raw,a.size,a.size)
    print(json.dumps(r,indent=2))
    if not r['protocol_cleanup_ok'] or r['status']!='window_finished':raise SystemExit(2)
if __name__=='__main__':main()
