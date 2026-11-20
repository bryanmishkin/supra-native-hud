#!/usr/bin/env python3
"""Offline transport fault injection against real road-list trial/session code.
Not a receiver or display simulator. Private accepted profile/reply required.
"""
import argparse,json,struct
from pathlib import Path
from road_list_expansion_trial import run
from ric_shared_trial import SharedSession,allocation_from_reply

def check(profile,reply):
    allocation=allocation_from_reply(reply[16:]);reports=[]
    def execute(case,fail_at=None,busy=None,interrupt=False,record_failure=False):
        occupied=set(()if busy is None else [busy]);calls=[];observed=[]
        def exchange(packet,timeout):
            svc,m,n,c,q,pv,iv,k,rc=struct.unpack('>HHIHHBBBB',packet[:16]);b=packet[16:]
            calls.append((m,b));payload=b''
            if m in (2,3,8):
                rid=int.from_bytes(b[4:8],'big')
                if m==2:payload=bytes([rid in occupied])
                elif m==3:
                    assert rid in (0x01000008,0x01000009);occupied.add(rid)
                else:
                    assert rid in (0x01000008,0x01000009);occupied.discard(rid)
            if len(calls)==fail_at:raise TimeoutError('Injected lost reply after request application')
            return struct.pack('>HHIHHBBBB',svc,m,len(payload)+8,c,q,1,1,128,0)+payload
        session=SharedSession(exchange,allocation,double_buffer=True)
        def observe(seconds):
            assert seconds==30;observed.append(seconds)
            if interrupt:raise KeyboardInterrupt('Injected cancellation')
        def record(r):
            if record_failure and r['cleanup']:raise OSError('Injected disk failure during cleanup')
        r=run(session,profile,case,record,observe)
        if record_failure:
            assert len(r['cleanup'])==7 and r['recording_errors'] and r['protocol_cleanup_passed']
        assert all(m not in (1,7)for m,_ in calls)
        if busy is not None:
            assert all(m==2 for m,_ in calls) and occupied=={busy}
        elif r['detachment_acknowledged']:
            assert not occupied,(case,fail_at,r)
        else:
            assert not any(m==8 for m,_ in calls),'Disposal after uncertain model detachment'
        return r,len(calls)
    for case in ('control','two_icons_one_entry','one_icon_two_entries'):
        clean,count=execute(case);assert clean['protocol_cleanup_passed'] and clean['status']=='window_finished'
        for i in range(1,count+1):execute(case,i)
        for rid in (0x01000008,0x01000009):execute(case,busy=rid)
        cancelled,_=execute(case,interrupt=True);assert cancelled['protocol_cleanup_passed']
        execute(case,record_failure=True)
        reports.append(dict(cleanup_survives_recording_failure=True,case=case,successful_request_count=count,lost_reply_positions_tested=count,occupied_slot_cases=2,cancellation_cleanup=True))
    return dict(cases=reports,vehicle_contact=False,limitation='Real trial/session code with injected correlated replies; not receiver acceptance, physical layout, or30second runtime evidence.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',type=Path,required=True);p.add_argument('--create-reply',type=Path,required=True);a=p.parse_args();print(json.dumps(check(a.profile.read_bytes(),a.create_reply.read_bytes()),indent=2))
