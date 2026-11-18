"""DisplaySink wire codec and bounded offline negotiation state.

No sockets, vehicle commands, or authority to draw. A negotiated sink is not
proof of physical pixel delivery. Implements the retained single-entry B009 SD
shape; other discovery bundles are deliberately rejected.
"""
import ipaddress
import math
import struct
from audit_pip_sink import decode


def subscription(ip, port, session, ttl=3, reboot=True):
    address=ipaddress.IPv4Address(ip)
    if address.is_multicast or address.is_unspecified or not 1<=port<=65535 or not 1<=session<=65535 or not 0<=ttl<=0xffffff:
        raise ValueError('invalid subscription endpoint/session/TTL')
    header=struct.pack('>HHIHHBBBB',0xffff,0x8100,48,0,session,1,1,2,0)
    entry=bytes([6,0,0,0x10])+struct.pack('>HHB',0xb009,1,1)+ttl.to_bytes(3,'big')+bytes(2)+struct.pack('>H',1)
    option=struct.pack('>HBB',9,4,0)+address.packed+bytes([0,6])+struct.pack('>H',port)
    return header+bytes([0xc0 if reboot else 0x40,0,0,0])+struct.pack('>I',16)+entry+struct.pack('>I',12)+option


def discovery(packet):
    if len(packet) not in (44,56):raise ValueError('not a single-entry sink discovery packet')
    h=struct.unpack('>HHIHHBBBB',packet[:16])
    if h[:3]!=(0xffff,0x8100,len(packet)-8) or h[3]!=0 or not h[4] or h[5:]!=(1,1,2,0):raise ValueError('invalid discovery header')
    if packet[16] not in (0x40,0xc0) or packet[17:20]!=bytes(3) or packet[20:24]!=struct.pack('>I',16):raise ValueError('invalid discovery flags/entry length')
    kind=packet[24];ttl=int.from_bytes(packet[33:36],'big')
    if packet[28:33]!=struct.pack('>HHB',0xb009,1,1) or packet[36:40]!=bytes.fromhex('00000001'):raise ValueError('wrong service/event group')
    result=dict(kind=kind,session=h[4],ttl=ttl,reboot=bool(packet[16]&0x80))
    if kind==6 and len(packet)==56:
        if packet[25:28]!=bytes.fromhex('000010') or packet[40:48]!=bytes.fromhex('0000000c00090400') or packet[52:54]!=bytes([0,6]):raise ValueError('invalid endpoint option')
        result.update(ip=str(ipaddress.IPv4Address(packet[48:52])),port=struct.unpack_from('>H',packet,54)[0])
        if subscription(result['ip'],result['port'],h[4],ttl,result['reboot'])!=packet:raise ValueError('noncanonical subscription')
    elif kind==7 and len(packet)==44:
        if packet[25:28]!=bytes(3) or packet[40:]!=bytes(4):raise ValueError('invalid acknowledgment')
    else:raise ValueError('unsupported discovery entry')
    return result


def completion(selection):
    if selection not in (0,1):raise ValueError('unknown sink selection')
    return struct.pack('>HHIHHBBBBBB',0xb009,1,10,1,0,1,1,1,0,selection,0)


class Negotiation:
    """State only; caller supplies bytes actually received and monotonic times.

    Tuple allowlist must come from target evidence, not requested canvas size.
    This class never declares windshield readiness or activates Guidance.
    """
    def __init__(self, supported):
        self.supported=frozenset(supported)
        self.lease_until=0.0;self.buffer=bytearray();self.pending=None;self.selected=None
        self.closed=False;self.failed=False

    def ack(self,packet,now):
        if self.closed or self.failed:raise ValueError('closed negotiation')
        row=discovery(packet)
        if row['kind']!=7:raise ValueError('expected subscription acknowledgment')
        if not math.isfinite(now) or now<0:raise ValueError('invalid clock')
        self.lease_until=now+row['ttl']
        if not row['ttl']:self.selected=None;self.pending=None

    def feed(self,data):
        if self.closed or self.failed:raise ValueError('closed negotiation')
        if len(self.buffer)+len(data)>4096:self.failed=True;raise ValueError('sink input exceeds bound')
        self.buffer.extend(data);answers=[]
        try:
            while len(self.buffer)>=16:
                n=struct.unpack_from('>I',self.buffer,4)[0]+8
                if not 16<=n<=64:raise ValueError('invalid sink frame size')
                if len(self.buffer)<n:break
                packet=bytes(self.buffer[:n]);del self.buffer[:n]
                # Retained SOME/IP magic cookie; no sink change implied.
                if packet==bytes.fromhex('ffff800000000008deadbeef01010200'):continue
                event=decode(packet)
                if event['type']!='selection':raise ValueError('expected sink selection')
                key=(event['scale'],event['width'],event['height'],event['selection'])
                self.selected=None
                if key not in self.supported:raise ValueError('unproven target sink tuple')
                if self.pending is not None:raise ValueError('selection arrived before completion was sent')
                self.pending=(key,completion(event['selection']));answers.append(self.pending[1])
        except ValueError:
            self.failed=True;self.selected=None;self.pending=None;raise
        return answers

    def completion_sent(self,packet,now):
        if self.closed or self.failed or self.pending is None or packet!=self.pending[1]:raise ValueError('unexpected completion')
        if not math.isfinite(now) or now<0 or now>=self.lease_until:raise ValueError('subscription not acknowledged or expired')
        self.selected=self.pending[0];self.pending=None

    def negotiated(self,now):
        return bool(not self.closed and not self.failed and self.selected is not None and math.isfinite(now) and 0<=now<self.lease_until)

    def close(self):
        self.closed=True;self.selected=None;self.pending=None;self.buffer.clear();self.lease_until=0
        # Transport owner must send TTL-zero unsubscribe and close its own sockets.
