#!/usr/bin/env python3
"""Offline cache/decoder and HUD name-selection experiments. No live binding.
Private older004 firmware required. Synthetic objects are explicitly identified.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.arm_const import *
SHA='50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761'
DATA_SHA='b33107cd3bc2b8133bea9b5636add414ce1a45aa6a43bc8b380a830fd7d92a58'

def verify(image,data,marker):
    b=image.read_bytes();d=data.read_bytes();encoded=(marker/'marker.rle32').read_bytes();pixels=(marker/'marker.bgra').read_bytes()
    assert hashlib.sha256(b).hexdigest()==SHA and hashlib.sha256(d).hexdigest()==DATA_SHA
    assert len(pixels)==408*132*4 and len(encoded)<=0x14000
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
    u.mem_map(0x10000,(len(b)+4095)&~4095);u.mem_write(0x10000,b)
    u.mem_map(0xc50000,0x23b0000);u.mem_write(0xc50000,d)
    u.mem_map(0x3000000,0x800000)
    stop=0x37ff000;stack=0x37fe000;app=0x3001000;cache=0x3300000;payload=0x3500000;decoded=0x3600000
    def call(pc,r0=0,r1=0,r2=0,r3=0,extra=b'',end=None):
        for reg,v in [(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop|1),(UC_ARM_REG_R0,r0),(UC_ARM_REG_R1,r1),(UC_ARM_REG_R2,r2),(UC_ARM_REG_R3,r3)]:u.reg_write(reg,v)
        if extra:u.mem_write(stack,extra)
        finish=end or stop;u.emu_start(pc|1,finish,count=3000000)
        assert u.reg_read(UC_ARM_REG_PC)==finish,hex(u.reg_read(UC_ARM_REG_PC))
        return u.reg_read(UC_ARM_REG_R0)
    # Both read/write cache pointers deliberately share synthetic storage; no commit cycle emulated.
    u.mem_write(app+0x1917c0,struct.pack('<II',cache,cache))
    for i in range(10):u.mem_write(cache+0x1c0+i*0x14010,b'\xff'*4)
    u.mem_write(payload,encoded)
    rid=0x01000008
    call(0x2b1ab0,app,rid,len(encoded),408,struct.pack('<II',132,payload))
    slot=call(0x2b21fe,app,rid)
    assert slot==cache+0x1c0
    assert struct.unpack('<IIHH',u.mem_read(slot,12))==(rid,len(encoded),408,132)
    assert bytes(u.mem_read(slot+12,len(encoded)))==encoded
    # Numeric key is not a factory selector. Execute the miss up to its logging boundary.
    missed=[]
    def logging(uc,a,size,data):
        if a==0x2dcb66:missed.append(a);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    loghook=u.hook_add(UC_HOOK_CODE,logging)
    assert call(0x2b21fe,app,0x5c)==0
    u.hook_del(loghook)
    allocations=[]
    def allocator(uc,a,size,data):
        if a==0x2d29e8:
            allocations.append(uc.reg_read(UC_ARM_REG_R0));uc.reg_write(UC_ARM_REG_R0,decoded);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    h=u.hook_add(UC_HOOK_CODE,allocator);u.mem_write(decoded,b'\xa5'*(len(pixels)+16))
    call(0x2d303c,408,132,len(encoded),0,struct.pack('<II',1,slot+12));u.hook_del(h)
    assert bytes(u.mem_read(decoded,len(pixels)))==pixels and bytes(u.mem_read(decoded+len(pixels),16))==b'\xa5'*16
    assert allocations==[len(pixels)]
    # Inspect the real selector->name->virtual-call slice with fake resource-manager methods.
    call(0x296efc,end=0x296f78)
    obj,mgr,vt=0x3003000,0x3005000,0x3006000
    u.mem_write(obj+0x10,struct.pack('<I',mgr));u.mem_write(mgr+0x1c,struct.pack('<I',vt))
    u.mem_write(vt+0x6c,struct.pack('<I',0x3701001));u.mem_write(vt+0x74,struct.pack('<I',0x3701011))
    current=[]
    def manager(uc,a,size,data):
        if a in (0x3701000,0x3701010):
            p=uc.reg_read(UC_ARM_REG_R1);name=bytes(uc.mem_read(p,160)).split(b'\0')[0].decode()
            current.append({'slot':hex(0x6c if a==0x3701000 else 0x74),'name':name,'r2':uc.reg_read(UC_ARM_REG_R2)})
            uc.reg_write(UC_ARM_REG_R0,0x3008000 if a==0x3701000 else 0);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    h=u.hook_add(UC_HOOK_CODE,manager);selectors=[]
    for selector in range(1,128):
        runs=[]
        for rgb in [(0,0,0),(8,0,1)]:
            current.clear();u.mem_write(obj+0x18,bytes([selector,*rgb,1,1]));u.reg_write(UC_ARM_REG_R5,obj)
            call(0x296d82,end=0x296dd6)
            assert len(current)==2 and current[0]['name']==current[1]['name'] and current[1]['r2']==0
            assert current[0]['name'].startswith('Imports#hud#hud_TestBmp#')
            runs.append(current[0]['name'])
        assert runs[0]==runs[1]
        selectors.append({'selector':selector,'resolved_name':runs[0],'rgb_does_not_change_name':True})
    u.hook_del(h)
    # KI built-in ID translation is a bounded table, not the upload cache.
    builtin_rows=[]
    for index in range(122):
        key=0x07000000+index
        names=[]
        for entry in (0x2562c4,0x2562ee):
            pointer=call(entry,key)
            names.append(bytes(u.mem_read(pointer,256)).split(b'\0')[0].decode() if pointer else None)
        builtin_rows.append({'id':hex(key),'names':names})
    rejected_ids=[0x01000008,0x5c,0x0700007a,0xffffffff]
    for key in rejected_ids:
        assert call(0x2562c4,key)==0 and call(0x2562ee,key)==0
    # The shared reference assignment used by both paths. This is NOT a network bridge.
    brush=0x3702000;old=0x3703000;new=0x3704000;src=0x3705000
    u.mem_write(brush+0x34,struct.pack('<I',old));u.mem_write(old+0x18,struct.pack('<I',2));u.mem_write(new+0x18,struct.pack('<I',1));u.mem_write(src,struct.pack('<I',new))
    call(0x2137d2,brush+0x34,src)
    assert struct.unpack('<I',u.mem_read(brush+0x34,4))[0]==new
    assert struct.unpack('<I',u.mem_read(old+0x18,4))[0]==1 and struct.unpack('<I',u.mem_read(new+0x18,4))[0]==2
    u.mem_write(src,struct.pack('<I',old));call(0x2137d2,brush+0x34,src)
    assert struct.unpack('<I',u.mem_read(brush+0x34,4))[0]==old
    assert struct.unpack('<I',u.mem_read(old+0x18,4))[0]==2 and struct.unpack('<I',u.mem_read(new+0x18,4))[0]==1
    return dict(passed=True,image_sha256=SHA,data_sha256=DATA_SHA,dimensions=[408,132],encoded_bytes=len(encoded),pixel_sha256=hashlib.sha256(pixels).hexdigest(),cache_insert_and_lookup_native=True,cache_synthetic_id=hex(rid),factory_selector_is_not_cache_key=True,decoder_matches=True,decoder_guard_unchanged=True,selectors=selectors,builtin_name_table=builtin_rows,builtin_rejected_ids=[hex(k) for k in rejected_ids],reference_swap_and_restore=True,
        intercepted={'cache_insert':[],'cache_lookup_miss':['logging 0x2dcb66'],'decoder':['allocator 0x2d29e8'],'selector_slice':['synthetic resource manager slots0x6c/0x74'],'reference_swap':[]},
        limits='Synthetic application/cache/brush/reference objects. Read and write buffers share one synthetic cache; buffer commit and concurrent access are not emulated. Native cache insertion and decoding do not establish transport admission or destination binding. Name lookup implementations, GPU rendering and physical output not executed. Shared reference swap is an offline ownership exercise, not callable remotely. No uploaded-image access to hud_TestBmp established.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--marker',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify(a.image,a.data,a.marker);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS:408x132 native cache/decoder,254 name-selection runs, reference swap/restore; no external binding claimed')
