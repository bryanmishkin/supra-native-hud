"""Differential XPD lookup tests against captured NavigationFully ARM."""
import argparse,json,struct
from style_xpd import Xpd,hash_component,FormatError,xar_entries
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--nav',required=True,type=Path);a=p.parse_args()
b=bytearray(512);struct.pack_into('<I',b,0,0x787064)
def node(off,key,kind=0,nxt=0,child=0):struct.pack_into('<IHHII',b,off,key,kind,0,nxt,child)
node(4,0,child=32);node(36,hash_component('guiding'),child=64);node(68,42,child=96);node(100,hash_component('viewStyle'),3)
struct.pack_into('<10I',b,116,9,1,2,3,4,5,6,7,8,9)
x=Xpd(b);results=[]
for names in [('guiding','viewStyle'),('guiding','8301','viewStyle'),('guiding','8301','extra','viewStyle'),('guiding','absent'),('missing',)]:
 keys=[hash_component(s) for s in names];py=x.lookup_hashes(keys)
 c=cpu_for(a.nav,NAV);db=BASE+0x1000;blob=BASE+0x2000;keyptr=BASE+0x3000;c.mem_write(blob,bytes(b));word(c,db+4,blob+4)
 for i,k in enumerate(keys):word(c,keyptr+i*4,k)
 for r,v in [(UC_ARM_REG_R0,db),(UC_ARM_REG_R1,blob+4),(UC_ARM_REG_R2,keyptr),(UC_ARM_REG_R3,len(keys)),(UC_ARM_REG_LR,BASE+0xf100)]:c.reg_write(r,v)
 c.emu_start(0x6366d0,BASE+0xf100,count=5000);raw=c.reg_read(UC_ARM_REG_R0);native=raw-blob if raw else None
 assert py==native,(names,py,native);results.append({'key':names,'node_offset':native})
assert x.int32_array(100)==list(range(1,10));assert len(x.view_definition(100)['elements'])==1
bad=bytearray(b);struct.pack_into('<I',bad,36+8,32);struct.pack_into('<I',bad,4+12,32)
try:Xpd(bad).lookup_hashes([1]);raise AssertionError('cycle accepted')
except FormatError:pass
try:xar_entries(bytes(31));raise AssertionError('short directory accepted')
except FormatError:pass
print(json.dumps({'native_sha256':NAV,'native_entry':'0x6366d0','cases':results,'external_callbacks':0,'negative_tests':['cycle rejected','short directory rejected'],'limitation':'Synthetic data differential proves lookup semantics only; no captured style DB or renderer admission claimed.'},indent=2))
