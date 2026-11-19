#!/usr/bin/env python3
"""Differential payload tests against exact captured ARM serializers, offline."""
import argparse,json,struct
from pathlib import Path
from verify_pip_binding_records import *
import guidance_payload as codec
STRING_SHA='d66bd39fab5fe8a7a72014025d95134ee84880ade1da93b3a5d5c55f9430f035'

def native_text(path,raw):
    c=cpu_for(path,STRING_SHA)
    stream,table,writer,obj,data=[BASE+i for i in (0x1000,0x2000,0x3000,0x4000,0x5000)]
    word(c,stream,table);word(c,table+0x18,writer);word(c,obj,data)
    word(c,data+8,len(raw));c.mem_write(data+0x11,raw+b'\0')
    chunks=[]
    def hook(cpu,a,size,user):
        if a in (0x17d6c,0x17ff4):
            cpu.reg_write(UC_ARM_REG_PC,{0x17d6c:0x18370,0x17ff4:0x18344}[a])
        elif a==writer:
            ptr,n=cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2)
            chunks.append(bytes(cpu.mem_read(ptr,n)) if n else b'')
            cpu.reg_write(UC_ARM_REG_R0,n);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
    c.hook_add(UC_HOOK_CODE,hook)
    c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,obj);c.reg_write(UC_ARM_REG_LR,BASE)
    c.emu_start(0x2dc68,BASE,count=300)
    assert c.reg_read(UC_ARM_REG_PC)==BASE
    return b''.join(chunks)

def native_payload(controller,strings,method,fields,options=()):
    c=cpu_for(controller,CTL)
    stream,table,writer,union,array,storage=[BASE+i for i in (0x1000,0x2000,0x3000,0x4000,0x5000,0x6000)]
    word(c,stream,table);word(c,table+0x18,writer);word(c,union,method)
    for i,value in enumerate(fields):word(c,union+0x10+4*i,value)
    if method==4 and options:
        word(c,union+0x24,array);word(c,union+0x28,array+8*len(options))
        for i,pair in enumerate(options):
            for j,value in enumerate(pair):
                raw=value.encode('utf-8');at=storage+512*(2*i+j)
                word(c,array+8*i+4*j,at);word(c,at+8,len(raw));c.mem_write(at+0x11,raw+b'\0')
    if method==8:
        word(c,union+0x1c,array);word(c,union+0x20,array+32)
        word(c,array,5);word(c,array+8,7);word(c,array+16,storage)
        raw=options[0][1].encode('utf-8')
        word(c,storage+8,len(raw));c.mem_write(storage+0x11,raw+b'\0')
    chunks=[]
    def hook(cpu,a,size,user):
        if a==writer:
            ptr,n=cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2)
            chunks.append(bytes(cpu.mem_read(ptr,n)) if n else b'')
            cpu.reg_write(UC_ARM_REG_R0,n);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        elif a==0x127400:
            obj=cpu.reg_read(UC_ARM_REG_R1);ptr=int.from_bytes(cpu.mem_read(obj,4),'little')
            n=int.from_bytes(cpu.mem_read(ptr+8,4),'little');raw=bytes(cpu.mem_read(ptr+0x11,n))
            chunks.append(native_text(strings,raw))
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
    c.hook_add(UC_HOOK_CODE,hook)
    c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,union);c.reg_write(UC_ARM_REG_LR,BASE)
    c.emu_start(0x1d3250,BASE,count=5000)
    assert c.reg_read(UC_ARM_REG_PC)==BASE
    return b''.join(chunks)

def verify(controller,strings):
    cases=[(3,[0,0x0300206d],[],codec.register_guidance(0,8301)),
           (2,[42,17],[],codec.attach_guidance(42,17)),
           (7,[],[],codec.unregister_guidance()),
           (4,[0x321,0,800,480],[],codec.register_displayable(0x321,0,800,480)),
           (4,[0x321,0,800,480],[('WindowCaption','1056')],codec.register_displayable(0x321,0,800,480,[('WindowCaption','1056')])),
           (4,[17,0,320,200],[('a','bc'),('empty','')],codec.register_displayable(17,0,320,200,[('a','bc'),('empty','')]))]
    cases.append((8,[42],[('content','RICManeuverID=17')],codec.set_ric_maneuver_content(42,17)))
    rows=[]
    for method,fields,options,expected in cases:
        actual=native_payload(controller,strings,method,fields,options)
        assert actual==expected,(method,actual.hex(),expected.hex())
        rows.append({'method':method,'fields':fields,'options':options,'hex':actual.hex(),'matches':True})
    for value in ('','a','1056','WindowCaption','é'):
        assert native_text(strings,value.encode())==codec.text(value)
    return {'controller_sha256':CTL,'string_library_sha256':STRING_SHA,'cases':rows,
            'boundary':'Actual generated union writer and captured CHBString writer; stream-write calls observed, PLT string call delegated to separate native library instance.',
            'vehicle_contact':False,'receiver_acceptance_proven':False,
            'limitation':'Synthetic serializer inputs, not permission to use factory user IDs/captions or a geometry claim. No network/service/session allocation executed.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--controller',type=Path,required=True);p.add_argument('--strings',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.controller,a.strings),indent=2))
