"""Conservative factory-guidance evidence reducer, not a live capture adapter.

Idle guidance does not prove radio/other overlays idle. An event can revoke an
experimental drawing lease; it never grants exclusive ownership or permission.
"""
import struct
from ric_graph import decode_graph_body
class FactoryActivity:
    def __init__(self,own_client=0x5348):
        self.own_client=own_client;self.guidance='unknown';self.at=None
    def observe(self,packet,at_ms):
        if self.at is not None and at_ms<self.at:
            self.guidance='unknown';return
        if len(packet)<16:raise ValueError('Truncated frame')
        service,method,length,client,session,pv,iv,kind,code=struct.unpack('>HHIHHBBBB',packet[:16])
        if length!=len(packet)-8:raise ValueError('Frame length mismatch')
        if (service,method,pv,iv,kind,code)!=(0xb006,9,1,1,0,0) or client==self.own_client:return
        decoded=decode_graph_body(method,packet[16:])
        if decoded.get('handle')!=200 or 'list_state' not in decoded:return
        state=decoded['list_state']['guidance_state']
        self.guidance='idle' if state==0 else 'active_or_transition';self.at=at_ms
    def blocks_drawing(self,now_ms):
        # Even observed guidance idle lacks radio-overlay and exclusive-lease evidence.
        return True
    def snapshot(self,now_ms):
        fresh=self.at is not None and 0<=now_ms-self.at<=300
        return dict(guidance=self.guidance if fresh else 'unknown',observed_at_ms=self.at,
                    radio='unknown',exclusive_ownership=False,drawing_allowed=False)
