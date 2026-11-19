"""Execute captured EGL format mapping and GLES readback channel conversion offline."""
import argparse,hashlib,json
from verify_pip_binding_records import *
p=argparse.ArgumentParser();p.add_argument('--egl',required=True,type=Path);p.add_argument('--gles',required=True,type=Path);a=p.parse_args()
e=hashlib.sha256(a.egl.read_bytes()).hexdigest();g=hashlib.sha256(a.gles.read_bytes()).hexdigest()
# These addresses apply only to the captured exact builds.
EGL_SHA='9dc7179f7515f63b2ff9c5422c8292af73c3263bcc0a3d85ce15ca181f10f762'
GLES_SHA='d4776fc2f6cf01668ca21b326338960e14b6d69510ca2f0e6b37cf72269ccf69'
# SHA recorded in output; reject a different captured file via constants set below.
if e!=EGL_SHA or g!=GLES_SHA:raise ValueError('Captured driver hash mismatch')
c=cpu_for(a.egl,e);obj=BASE+0x1000;sp=BASE+0xf000;c.reg_write(UC_ARM_REG_R5,obj);word(c,sp+0x14,2);word(c,obj+0x14,17)
c.emu_start(0x64c4,0x6510,count=100)
fmt=int.from_bytes(c.mem_read(obj+12,4),'little');stride=int.from_bytes(c.mem_read(obj+0x14,4),'little');assert fmt==20 and stride==68
c=cpu_for(a.gles,g);desc=BASE+0x1000;src=BASE+0x2000;dst=BASE+0x3000
raw=bytes.fromhex('11223344a1b2c3d4');c.mem_write(src,raw)
for off,v in [(8,2),(0x1c,4),(0x28,src),(0x2c,dst)]:word(c,desc+off,v)
c.reg_write(UC_ARM_REG_R0,desc);c.reg_write(UC_ARM_REG_LR,BASE+0xf100);c.emu_start(0x2f000,BASE+0xf100,count=100)
converted=bytes(c.mem_read(dst,8));assert converted.hex()=='33221144c3b2a1d4'
print(json.dumps({'egl_sha256':e,'gles_sha256':g,'wsegl_format':2,'internal_format':fmt,'stride_pixels':17,'stride_bytes':stride,'framebuffer_bytes':raw.hex(),'gl_rgba_unsigned_byte_readback':converted.hex(),'channel_permutation':[2,1,0,3],'intercepts':[],'limitation':'Actual native format mapping and CPU readback converter verified. This establishes BGRA framebuffer bytes for WSEGL enum2; it does not execute GPU hardware, compositor or remote display transport.'},indent=2))
