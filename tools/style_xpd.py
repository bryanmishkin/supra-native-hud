"""Bounded decoder of native-traced XAR directory and XPD node graph.
Not a complete format validator; unknown headers/types remain uninterpreted.
"""
import struct
TAGS={0x787064:'XPD',0x787264:'XRD',0x32465058:'XPF2',0x33465058:'XPF3',0x64336778:'XG3D'}
class FormatError(ValueError):pass
class Blob:
 def __init__(self,data):self.data=data
 def get(self,off,fmt):
  n=struct.calcsize(fmt)
  if off<0 or off+n>len(self.data):raise FormatError(f'out of bounds {off:#x}+{n}')
  return struct.unpack_from(fmt,self.data,off)[0]
 def u32(self,o):return self.get(o,'<I')
 def u16(self,o):return self.get(o,'<H')
def hash_component(value):
 h=0
 for b in value.encode('utf-8'):h=(37*h+(b if b<128 else b-256))&0xffffffff
 return h

def guiding_view_keys(view_id):
 """62d0fc uses component index2: append signed decimal to viewStyle."""
 if not -(1<<31)<=view_id<(1<<31):raise FormatError("view ID outside int32")
 return [hash_component("guiding"),hash_component("*"),hash_component("viewStyle"+str(view_id))]

def xar_entries(data,max_entries=65536):
 b=Blob(data);n=b.u32(0x1c)
 if n>max_entries or 0x20+4*n>len(data):raise FormatError('invalid directory count')
 result=[]
 for i in range(n):
  rel=b.u32(0x20+4*i)
  if not rel:continue
  off=rel*4;tag=b.u32(off)
  result.append({'index':i,'offset':off,'tag':tag,'kind':TAGS.get(tag,'unknown')})
 return result

class Xpd:
 def __init__(self,data,tag_offset=0,max_nodes=65536):
  self.b=Blob(data);self.base=tag_offset+4;self.max_nodes=max_nodes
  if self.b.u32(tag_offset)!=0x787064:raise FormatError('not XPD tag')
  self.b.get(self.base+15,'B')
 def node(self,off):
  b=self.b
  return {'offset':off,'key':b.u32(off),'type':b.u16(off+4),'next':b.u32(off+8),'child':b.u32(off+12)}
 def child(self,parent,key):
  rel=self.node(parent)['child'];seen=set()
  while rel:
   off=self.base+rel
   if off in seen or len(seen)>=self.max_nodes:raise FormatError('cycle or node budget')
   seen.add(off);n=self.node(off)
   if n['key']==key:return off
   rel=n['next']
  return None
 def lookup_hashes(self,keys):
  if not keys or len(keys)>13:raise FormatError('key count must be 1..13')
  budget=[self.max_nodes]
  def find(parent,ks):
   budget[0]-=1
   if budget[0]<0:raise FormatError('lookup budget')
   hit=self.child(parent,ks[0])
   if len(ks)==1:return hit
   if hit is not None:
    result=find(hit,ks[1:])
    if result is not None:return result
   wild=self.child(parent,0x2a)
   if wild is not None:
    for i in range(1,len(ks)):
     result=find(wild,ks[i:])
     if result is not None:return result
   return None
  return find(self.base,keys)
 def int32_array(self,node_offset):
  if self.node(node_offset)['type']!=3:raise FormatError('not INT32_ARRAY')
  p=node_offset+16
  if p%4:raise FormatError('unaligned array')
  n=self.b.u32(p)
  if n>self.max_nodes or p+4+4*n>len(self.b.data):raise FormatError('array bounds/budget')
  return [self.b.u32(p+4+4*i) for i in range(n)]
 def view_definition(self,node_offset):
  words=self.int32_array(node_offset)
  if len(words)<=8:raise FormatError('native rejects <=8 words')
  # Native integer division ignores incomplete tail; report it, never hide it.
  return {'header':words[:4],'elements':[words[i:i+5] for i in range(4,len(words)-4,5)],'trailing_words':words[4+((len(words)-4)//5)*5:]}

if __name__=='__main__':
 import argparse,json
 from pathlib import Path
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--xpd-offset',type=lambda x:int(x,0));p.add_argument('--key',action='append',help='Explicit component; repeat for each hierarchy level. Append decimal style index exactly when required.');p.add_argument('--guiding-view-id',type=int);p.add_argument('--view',action='store_true');a=p.parse_args();data=a.input.read_bytes()
 if len(data)>256*1024*1024:p.error('input exceeds256MiB limit')
 if a.xpd_offset is None:out={'entries':xar_entries(data),'limitation':'Directory only; unknown tags retained. Use an XPD entry offset for property lookup.'}
 else:
  x=Xpd(data,a.xpd_offset)
  if not a.key and a.guiding_view_id is None:p.error('--key or --guiding-view-id required')
  keys=guiding_view_keys(a.guiding_view_id) if a.guiding_view_id is not None else [hash_component(k) for k in a.key];off=x.lookup_hashes(keys);out={'hashes':keys,'node':x.node(off) if off is not None else None}
  if off is not None:out['value']=x.view_definition(off) if a.view else x.int32_array(off)
 print(json.dumps(out,indent=2))
