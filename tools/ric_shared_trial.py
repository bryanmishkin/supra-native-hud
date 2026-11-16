"""Explicit shared-factory-session trial support. Never create/dispose the instance.

Only a live-verified configuration may supply IDs. A free resource check is
not exclusive allocation; factory guidance must remain stopped during use.
"""
import struct
from ric_owned_session import OwnedSession,RicFailure
from ric_lifecycle import Reader,decode_bitmap_config
from ric_live_trial import DrawingTrial
from ric_rle32 import encode_bgra,marker_bgra


def allocation_from_reply(reply):
    r=Reader(reply);handle=r.u32();a=Reader(r.take(r.u32()));r.finish()
    models={};bitmap=None
    while a.pos<len(a.data):
        n,tag=a.u32(),a.u32();raw=a.take(n)
        if tag==33:
            if bitmap is not None:raise RicFailure('Ambiguous bitmap configuration')
            bitmap=decode_bitmap_config(raw)
        if tag in (1,4,17,18,20,21,30) and len(raw)>=10:
            kind,typ,count,offset=struct.unpack_from('>BBII',raw)
            if (typ,tag) in ((10,1),(15,17),(32,20),(33,21),(34,1),(29,18),(17,4),(40,30)):
                if typ in models or not count or offset+count>0xffffffff:raise RicFailure('Invalid model allocation')
                models[typ]=offset+count-1
    if handle!=200 or not {10,15,32,33}.issubset(models):raise RicFailure('Unexpected shared profile')
    if not bitmap or not bitmap['formats']['rle32'] or bitmap['resolution_pair']!=[150,36]:raise RicFailure('Verified RLE32 profile required')
    n=bitmap['resource_element_count'];off=bitmap['resource_element_offset']
    if not 1<=n<=32 or off+n>0xffffffff:raise RicFailure('Invalid resource range')
    return dict(handle=handle,models=models,resource_id=off+n-1,resource_type=bitmap['resource_type'],
                dimensions=[150,36],resource_ids=list(range(off,off+n)))


class SharedSession(OwnedSession):
    """Adopts explicitly confirmed shared handle; close removes only our upload."""
    def __init__(self,exchange,allocation,client_id=0x5348):
        super().__init__(exchange,('SupraHUD.ResourceTrial','SupraHUD.Test','bryanmishkin'),(3,3,1),client_id,timeout=2)
        if allocation['handle']!=200:raise RicFailure('Unexpected shared handle')
        self.handle=allocation['handle'];self.state='created';self.allocation=allocation
    def open(self):raise RicFailure('Shared trial must not create an instance')
    def _request(self,method,body):
        if method not in (2,3,4,8,9,10,11,12,14):raise RicFailure('Method forbidden in shared trial')
        if len(body)<4 or struct.unpack_from('>I',body)[0]!=self.handle:raise RicFailure('Wrong handle')
        if method in (2,3,8):
            if len(body)<8:raise RicFailure('Missing resource ID')
            rid=struct.unpack_from('>I',body,4)[0]
            if rid not in self.allocation.get('resource_ids',[]):raise RicFailure('Resource outside confirmed bitmap range')
            if method==3 and rid!=self.allocation['resource_id']:raise RicFailure('Upload outside selected slot')
        if method in (9,10,11,12,14):
            if len(body)<9:raise RicFailure('Missing model identity')
            mid=struct.unpack_from('>I',body,4)[0];typ=body[8]
            if self.allocation.get('models',{}).get(typ)!=mid:raise RicFailure('Model outside selected allocation')
        if method==8 and struct.unpack_from('>I',body,4)[0] not in self.resources:raise RicFailure('Cannot remove untracked resource')
        return super()._request(method,body)
    def close(self):
        if self.cleanup_report is not None:return self.cleanup_report
        report=dict(shared_instance_preserved=True,resources=[],remote_image_erased=False,visual_test_passed=False)
        self.cleanup_report=report
        for rid,typ in self.resources.items():
            row=dict(resource_id=rid,dispose_acknowledged=False,post_dispose_check=None,errors=[]);report['resources'].append(row)
            try:self._empty(8,struct.pack('>II',self.handle,rid));row['dispose_acknowledged']=True
            except Exception as e:row['errors'].append(str(e))
            try:row['post_dispose_check']=self._check(rid,typ)
            except Exception as e:row['errors'].append(str(e))
        self.state='closed';return report
    def preflight(self):
        # Require the whole advertised bitmap pool empty, not just our last slot.
        states={i:self.check(i,self.allocation['resource_type']) for i in self.allocation['resource_ids']}
        if any(states.values()):raise RicFailure('Factory bitmap pool is in use')
        return states
    def upload_marker(self):
        a=self.allocation
        self.upload_bitmap(a['resource_id'],a['resource_type'],a['dimensions'],encode_bgra(marker_bgra(*a['dimensions'])))

class SharedDrawingTrial(DrawingTrial):
    """Stopped-guidance experiment using shared singleton list/state controls.

    Not an independent overlay. Factory guidance must stay stopped throughout.
    Highest advertised description/high-picture slots are used; they are not
    exclusively allocated. Cancel/idle and empty list restore stopped guidance.
    """
    def run(self):
        from ric_graph import encode_description_body
        from ric_guiding import encode_high_roundabout_body
        from ric_live_trial import ABSENT,list_body
        self.result['shared_instance']=True
        self.result['own_session_accepted']=False
        try:
            self.allocation=self.session.allocation
            self.result['allocation']=self.allocation
            self.result['preflight']=self.session.preflight()
            self.session.upload_marker()
            self.result['upload_and_presence_confirmed']=True
            a,h=self.allocation,self.session.handle
            self.graph_started=True;self.result['status']='graph_attempt';self.save()
            self.send(9,self.state(1))
            self.send(11,encode_high_roundabout_body(h,a['models'][10],10,0,2,a['resource_id']))
            self.send(10,encode_description_body(h,a['models'][15],15,is_passive=False,
                previous_joined=False,previous_maneuver_id=ABSENT,next_joined=False,
                next_maneuver_id=ABSENT,maneuver_direction=8,current_state_id=ABSENT,
                coming_road_id=ABSENT,detailed_maneuver_id=a['models'][10],distance_id=ABSENT,
                navigation_event_ids=[],lane_guiding_ids=[],point_of_interest_ids=[]))
            self.send(12,list_body(h,a['models'][32],a['models'][15]))
            self.send(4,struct.pack('>I',h))
            self.send(9,self.state(2,a['models'][15]))
            self.result['status']='observing_marker';self.save()
            self.result['windshield_marker_seen']=self.observe('marker',15)
        except (Exception,KeyboardInterrupt) as e:
            self.result['status']='failed_or_interrupted';self.result['error']=str(e) or type(e).__name__
        finally:
            self.begin_cleanup()
            try:self.withdraw()
            finally:self.result['cleanup']=self.session.close();self.save()
        if self.result['status']!='failed_or_interrupted':self.result['status']='awaiting_visual_verification'
        self.save();return self.result
