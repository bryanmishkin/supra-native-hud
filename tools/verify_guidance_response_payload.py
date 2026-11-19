#!/usr/bin/env python3
"""Run native response union decoder; distinguish reply payload from retained request sequence."""
import argparse
import json
import struct
from pathlib import Path
from verify_pip_binding_records import *


def verify(path):
    rows=[]
    for guidance,status,sequence in [(42,0,37),(0,2,51),(0x12345678,1,93)]:
        c=cpu_for(path,CTL)
        stream,table,reader,union,proxy,event,call= [BASE+i for i in (0x1000,0x2000,0x3000,0x4000,0x5000,0x6000,0x7000)]
        word(c,stream,table);word(c,table+0x18,reader);word(c,union,0x80000000)
        raw=struct.pack('<II',guidance,status);position=0
        def read(cpu,address,size,user):
            nonlocal position
            if address==reader:
                count=cpu.reg_read(UC_ARM_REG_R2);destination=cpu.reg_read(UC_ARM_REG_R1)
                assert count==4 and position+count<=len(raw)
                cpu.mem_write(destination,raw[position:position+count]);position+=count
                cpu.reg_write(UC_ARM_REG_R0,count);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
            elif address==0xc26c34:
                # Execute accessor natively; no interception here.
                pass
        c.hook_add(UC_HOOK_CODE,read)
        c.reg_write(UC_ARM_REG_R0,stream);c.reg_write(UC_ARM_REG_R1,union);c.reg_write(UC_ARM_REG_LR,BASE)
        c.emu_start(0x1d30d4,BASE,count=200)
        assert position==8 and bytes(c.mem_read(union+0x10,8))==raw
        word(c,proxy+0x94,event);word(c,event+0x28,0x80000000);c.mem_write(event+0x50,raw)
        word(c,call+4,sequence)
        context=BASE+0x8000;word(c,context+0xa8,proxy)
        c.reg_write(UC_ARM_REG_R1,call);c.reg_write(UC_ARM_REG_R2,context)
        # Stop before unrelated task-completion dispatcher, after actual accessor/copy.
        c.emu_start(0x3109ac,0x3109c8,count=100)
        actual=struct.unpack('<II',bytes(c.mem_read(call,8)))
        assert actual==(guidance,sequence)
        rows.append({'wire_words':[guidance,status],'retained_sequence':sequence,'local_completion_words':list(actual)})
    return {'sha256':CTL,'cases':rows,'wire_second_field_semantics':'not established by this decoder; not the retained MOCCA request sequence',
            'boundary':'Native decoder, accessor and local copy; stream read intercepted, completion delivery not executed.',
            'vehicle_contact':False,'receiver_acceptance_proven':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path)
    print(json.dumps(verify(p.parse_args().controller),indent=2))
