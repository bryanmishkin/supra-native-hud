#!/usr/bin/env python3
"""Execute native DNAVIManeuverView method-3 payload writer, offline only.
The observed stream-write boundary is not a complete MOCCA transport envelope.
"""
import argparse
import json
import struct
from pathlib import Path
from verify_pip_binding_records import cpu_for, word, BASE, CTL
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC


def verify(path):
    rows=[]
    for maneuver, kind in [(0,0x0300206d),(0xfffffffe,0x030020d2),(123,0x030010cd)]:
        cpu=cpu_for(path,CTL)
        stream, table, writer, union = BASE+0x1000,BASE+0x2000,BASE+0x3000,BASE+0x4000
        word(cpu,stream,table);word(cpu,table+0x18,writer)
        word(cpu,union,3);word(cpu,union+4,8)
        cpu.mem_write(union+0x10,struct.pack('<II',maneuver,kind))
        chunks=[]
        def observe(c,a,size,user):
            if a==writer:
                assert c.reg_read(UC_ARM_REG_R0)==stream
                n=c.reg_read(UC_ARM_REG_R2)
                assert n==4
                chunks.append(bytes(c.mem_read(c.reg_read(UC_ARM_REG_R1),n)))
                c.reg_write(UC_ARM_REG_R0,n)
                c.reg_write(UC_ARM_REG_PC,c.reg_read(UC_ARM_REG_LR))
        cpu.hook_add(UC_HOOK_CODE,observe)
        cpu.reg_write(UC_ARM_REG_R0,stream);cpu.reg_write(UC_ARM_REG_R1,union);cpu.reg_write(UC_ARM_REG_LR,BASE)
        cpu.emu_start(0x1d3250,BASE,count=200)
        assert cpu.reg_read(UC_ARM_REG_PC)==BASE
        payload=b''.join(chunks)
        assert payload==struct.pack('<II',maneuver,kind)
        rows.append({'maneuver_id':maneuver,'style_client':kind>>24,'guidance_type':kind&0xffffff,'payload_hex':payload.hex(),'write_sizes':list(map(len,chunks))})
    return {'sha256':CTL,'native_dispatch':'0x1d3250','method3_payload_writer':'0x1d6df8','cases':rows,'boundary':'IHBOStream virtual write; final transport framing and endian transformations downstream not executed','vehicle_contact':False,'receiver_acceptance_proven':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('controller',type=Path)
    print(json.dumps(verify(p.parse_args().controller),indent=2))
