#!/usr/bin/env python3
"""Exercise actual trial/session code with lost/rejected replies. No renderer simulation."""
import argparse,json,struct
from pathlib import Path
from destination_surface_plan import compile_plan,run
from ric_shared_trial import SharedSession,allocation_from_reply

def check(profile,reply,witness):
    plan=compile_plan(profile,reply,witness)
    allocation=allocation_from_reply(reply[16:]);allocation['models'][49]=plan['model_id']
    def execute(fail_at=None,reject_at=None,busy=None,interrupt=False,record_failure=False):
        occupied=set(() if busy is None else [busy]);calls=[];observed=[]
        def exchange(packet,timeout):
            svc,m,n,c,q,pv,iv,k,rc=struct.unpack('>HHIHHBBBB',packet[:16]);b=packet[16:]
            calls.append((m,b));payload=b'';code=1 if len(calls)==reject_at else 0
            if m in (2,3,8):
                rid=int.from_bytes(b[4:8],'big')
                if m==2:payload=bytes([rid in occupied])
                elif not code:
                    if m==3:occupied.add(rid)
                    else:occupied.discard(rid)
            if len(calls)==fail_at:raise TimeoutError('Lost reply after applied request')
            return struct.pack('>HHIHHBBBB',svc,m,len(payload)+8,c,q,1,1,128,code)+payload
        session=SharedSession(exchange,allocation,double_buffer=True)
        def observe(seconds):
            assert seconds==30;observed.append(seconds)
            if interrupt:raise KeyboardInterrupt()
        def record(value):
            if record_failure and value['cleanup']:raise OSError('Journal unavailable')
        r=run(session,plan,record,observe)
        assert all(m not in (1,7) for m,_ in calls)
        if busy is not None:assert all(m==2 for m,_ in calls) and occupied=={busy}
        elif not r['detachment_acknowledged']:
            assert not any(m==8 for m,_ in calls),'Disposal despite uncertain detachment'
        elif r['protocol_cleanup_passed']:assert not occupied
        if r['graph_attempted'] and r['detachment_acknowledged']:
            clear=next(i for i,(m,b) in enumerate(calls) if m==11 and b[8]==49 and b[-4:]==b'\xff'*4)
            deletes=[i for i,(m,b) in enumerate(calls) if m==8]
            assert all(clear<i for i in deletes)
        if not any((fail_at,reject_at,busy,interrupt,record_failure)):
            assert observed==[30] and r['status']=='window_finished' and r['protocol_cleanup_passed']
        if record_failure:assert len(r['cleanup'])==8 and r['recording_errors'] and r['protocol_cleanup_passed']
        return r,len(calls)
    clean,count=execute()
    for i in range(1,count+1):execute(fail_at=i);execute(reject_at=i)
    for rid in (0x01000008,0x01000009):execute(busy=rid)
    assert execute(interrupt=True)[0]['protocol_cleanup_passed']
    execute(record_failure=True)
    return dict(case=plan['case'],normal_requests=count,lost_reply_positions=count,rejected_reply_positions=count,
        busy_slots_tested=2,cancellation_cleanup=True,journal_failure_cleanup=True,
        no_dispose_when_detachment_uncertain=True,native_receiver_simulated=False,vehicle_contact=False,
        physical_extent_proven=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,required=True);p.add_argument('--reply',type=Path,required=True);p.add_argument('--witness',type=Path,required=True);a=p.parse_args()
    print(json.dumps(check(a.profile.read_bytes(),a.reply.read_bytes(),a.witness.read_bytes()),indent=2))
