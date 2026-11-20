#!/usr/bin/env python3
"""Socket/subprocess orchestration checks. Does not simulate Screen or a receiver renderer."""
import argparse,json,socket,struct,sys,tempfile,threading
from pathlib import Path
from run_corrected_pip_trial import plan,producer_contract,run,Session,TcpExchange

def verify(profile,reply):
 rows=[]
 for mode in ['complete','missing-handshake','description-rejected','hud-complete','hud-description-rejected']:
  a=plan(reply,profile,'day',69 if mode.startswith('hud-') else 461);a['allow_hud_candidate']=mode.startswith('hud-');client,peer=socket.socketpair();present=set();packets=[];errors=[]
  def read(n):
   data=bytearray()
   while len(data)<n:
    part=peer.recv(n-len(data))
    if not part:raise EOFError()
    data.extend(part)
   return bytes(data)
  def server():
   try:
    while True:
     h=read(16);body=read(struct.unpack_from('>I',h,4)[0]-8);m=struct.unpack_from('>H',h,2)[0]
     packets.append((m,body));assert m not in (1,7,14)
     code=0;result=b''
     if m in (2,3,8):
      rid=struct.unpack_from('>I',body,4)[0]
      if m==3:present.add(rid)
      if m==8:present.discard(rid)
      if m==2:result=bytes([rid in present])
     if mode.endswith('description-rejected') and m==10 and body[8]==15:code=1
     response=bytearray(h);response[4:8]=struct.pack('>I',8+len(result));response[14]=128;response[15]=code
     peer.sendall(response+result)
   except EOFError:pass
   except BaseException as e:errors.append(repr(e))
   finally:peer.close()
  thread=threading.Thread(target=server);thread.start()
  try:
   with tempfile.TemporaryDirectory(prefix='supra-corrected-lifecycle-') as temp:
    t=Path(temp);go=t/'go';stop=t/'stop';helper=t/'fixture.py'
    text="import time\nfrom pathlib import Path\n"
    if mode!='missing-handshake':text+="print("+repr("SINK_NEGOTIATED_HUD_CANDIDATE" if mode.startswith("hud-") else "SINK_NEGOTIATED_CLUSTER")+",flush=True)\n"
    contract=producer_contract(a)
    if mode.startswith('hud-'):contract['selection']=0
    text+='print('+repr('PIP_BINDING '+json.dumps(contract))+',flush=True)\n'
    text+="print('PRODUCER_READY',flush=True)\n"
    text+='go=Path('+repr(str(go))+'); stop=Path('+repr(str(stop))+')\n'
    text+="end=time.monotonic()+5\nwhile not go.exists() and not stop.exists() and time.monotonic()<end: time.sleep(.01)\n"
    text+="if go.exists(): print('VISIBLE_WINDOW_STARTED',flush=True); time.sleep(.05)\n"
    text+="print('PRODUCER_END local_cleanup=1 unsubscribe_sent=1 full_visible_window=1',flush=True)\n"
    helper.write_text(text)
    touch=lambda p:[sys.executable,'-c','from pathlib import Path; Path('+repr(str(p))+').touch()']
    result=run(Session(TcpExchange(client,t),a),a,[sys.executable,str(helper)],lambda r:None,touch(go),touch(stop))
    assert result['protocol_cleanup'] and result['local_cleanup'] and result['resource_absent']
    assert (result['status']=='finished')==(mode in ('complete','hud-complete'))
    if mode=='missing-handshake':assert not result['graph_attempted']
  finally:client.close();thread.join(5)
  assert not thread.is_alive() and not errors and not present
  if result['graph_attempted']:
   clear=next(i for i,(m,b) in enumerate(packets) if m==11 and b[-4:]==b'\xff'*4)
   dispose=next(i for i,(m,b) in enumerate(packets) if m==8)
   assert clear<dispose
  rows.append(dict(case=mode,requests=len(packets),cleanup=True,resource_absent=True,status=result['status']))
 return dict(cases=rows,real_socket_and_subprocess=True,renderer_simulated=False,vehicle_contact=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,required=True);p.add_argument('--create-response',type=Path,required=True);a=p.parse_args()
 print(json.dumps(verify(a.profile.read_bytes(),a.create_response.read_bytes()),indent=2))
