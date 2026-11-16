"""Assess parsed capture evidence without granting ownership or startup completeness."""
import hashlib,struct
from audit_model_sessions import audit
TARGETS={0xb006,0xb009,0xb00e}
def assess(parsed):
    valid=[s for s in parsed['streams'] if not s['parse_error']]
    transactions=audit([(s['flow'],s['data']) for s in valid]);events=[]
    for s in valid:
        data=s['data'];pos=0
        while pos<len(data):
            svc,method,n,client,session,pv,iv,kind,rc=struct.unpack_from('>HHIHHBBBB',data,pos);end=pos+n+8
            if svc in TARGETS:
                times=[p['timestamp_us'] for p in s['byte_spans'] if p['offset']<end and p['offset']+p['bytes']>pos]
                events.append(dict(flow=s['flow'],service=svc,method=method,kind=kind,client=client,session=session,interface=iv,result=rc,body_bytes=n-8,body_sha256=hashlib.sha256(data[pos+16:end]).hexdigest(),packet_time_min_us=min(times) if times else None,packet_time_max_us=max(times) if times else None))
            pos=end
    create=[t for t in transactions['transactions'] if t['service']==0xb006 and t['method']==1 and t['status']=='ok' and t['interface']==1]
    return dict(transactions=transactions,events=events,matched_guidance_create=len(create),all_streams_parse=len(valid)==len(parsed['streams']),
                independent_surface_proven=False,startup_covered=False,
                limitation='Packet-time bounds include retransmissions; not an exact application timestamp. Matched creation proves protocol acceptance only, not ownership, initialization, release, supported drawing or full startup coverage.')
