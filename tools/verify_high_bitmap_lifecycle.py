#!/usr/bin/env python3
"""Exercise the real TCP client and cleanup; peer only acknowledges wire packets.

No vehicle or rendering simulation. Requires the preserved private profile.
"""
import argparse,json,socket,struct,tempfile,threading
from pathlib import Path
from b006_high_bitmap import build_candidate
from run_high_bitmap_trial import HighTrial
from ric_shared_trial import SharedSession,allocation_from_reply
from ric_live_trial import TcpExchange

def verify(profile,reply):
 allocation=allocation_from_reply(reply[16:]);rows=[]
 for mode in ['complete','interrupt','description-rejected']:
  candidate=build_candidate(profile,allocation,threshold=1000.0)
  client,peer=socket.socketpair();packets=[];present=set();errors=[]
  def read(n):
   b=bytearray()
   while len(b)<n:
    k=peer.recv(n-len(b))
    if not k:raise EOFError()
    b.extend(k)
   return bytes(b)
  def server():
   try:
    while True:
     h=read(16);body=read(struct.unpack_from('>I',h,4)[0]-8)
     m=struct.unpack_from('>H',h,2)[0];packets.append((m,body))
     assert m not in (1,7,14), 'No instance create/dispose or road-icon changes'
     code=0
     if m in (2,3,8):
      rid=struct.unpack_from('>I',body,4)[0]
      if m==3:present.add(rid)
      if m==8:present.discard(rid)
      result=bytes([rid in present]) if m==2 else b''
     else:
      result=b''
      if mode=='description-rejected' and m==10 and body[8]==15:code=1
     response=bytearray(h);response[4:8]=struct.pack('>I',8+len(result));response[14]=128;response[15]=code
     peer.sendall(response+result)
   except EOFError:pass
   except BaseException as e:errors.append(repr(e))
   finally:peer.close()
  thread=threading.Thread(target=server);thread.start()
  def observe(phase,seconds):
   if mode=='interrupt':raise KeyboardInterrupt()
   return None
  try:
   with tempfile.TemporaryDirectory(prefix='supra-high-lifecycle-') as t:
    result=HighTrial(SharedSession(TcpExchange(client,t),allocation),candidate,lambda r:None,observe,lambda:None).run()
  finally:client.close();thread.join(5)
  assert not thread.is_alive() and not errors and not present
  assert all(x['acknowledged'] for x in result['cleanup_steps'])
  assert all(x['dispose_acknowledged'] and x['post_dispose_check'] is False for x in result['cleanup']['resources'])
  current=[b for m,b in packets if m==10 and b[8]==34]
  assert len(current)==1 and struct.unpack_from('>d',current[0],38)[0]==1000.0
  clear=next(i for i,(m,b) in enumerate(packets) if m==11 and b[-4:]==b'\xff'*4)
  disposal=next(i for i,(m,b) in enumerate(packets) if m==8)
  restored=next(i for i,(m,b) in enumerate(packets) if m==9 and b==candidate['position_stop'])
  assert clear<restored<disposal
  rows.append(dict(case=mode,requests=len(packets),cleanup_acknowledged=True,resource_absent=True,shared_instance_preserved=True))
 return dict(cases=rows,real_socket_transport=True,renderer_simulated=False,vehicle_contact=False,larger_area_verified=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,required=True);p.add_argument('--create-response',type=Path,required=True);a=p.parse_args()
 print(json.dumps(verify(a.profile.read_bytes(),a.create_response.read_bytes()),indent=2))
