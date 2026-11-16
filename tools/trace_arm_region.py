#!/usr/bin/env python3
"""Read-only ARM ELF evidence extraction. Never executes the inspected binary.
Regions may contain literal pools: decoded instructions are not proof of reachable code.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from capstone.arm import ARM_OP_MEM,ARM_REG_PC,ARM_INS_LDR

def read_virtual(data,segments,address,size):
    if size<0:raise ValueError('Negative read')
    for va,offset,length in segments:
        if va<=address and address+size<=va+length:return data[offset+address-va:offset+address-va+size]
    raise ValueError('Address is outside file-backed segments')

def trace(path,address,size,words=False):
    if size<=0 or size>16384 or address%4 or size%4:raise ValueError('Use aligned regions of 4..16384 bytes')
    if path.stat().st_size>64*1024*1024:raise ValueError('ELF exceeds 64 MiB limit')
    data=path.read_bytes()
    with path.open('rb') as f:
        elf=ELFFile(f)
        if elf.elfclass!=32 or not elf.little_endian or elf['e_machine']!='EM_ARM':raise ValueError('Expected ARM32 little-endian ELF')
        segments=[(s['p_vaddr'],s['p_offset'],s['p_filesz']) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
        raw=read_virtual(data,segments,address,size);rows=[]
        if words:
            rows=[{'address':hex(address+i),'value':hex(struct.unpack_from('<I',raw,i)[0])} for i in range(0,size,4)]
        else:
            md=Cs(CS_ARCH_ARM,CS_MODE_ARM);md.detail=True
            for ins in md.disasm(raw,address):
                row={'address':hex(ins.address),'instruction':ins.mnemonic+' '+ins.op_str}
                for op in ins.operands:
                    if op.type==ARM_OP_MEM and op.mem.base==ARM_REG_PC and ins.id==ARM_INS_LDR:
                        literal=ins.address+8+op.mem.disp
                        try:
                            value=struct.unpack('<I',read_virtual(data,segments,literal,4))[0]
                            row['pc_relative_word_address']=hex(literal);row['pc_relative_word']=hex(value)
                            try:
                                text=read_virtual(data,segments,value,192).split(b'\0',1)[0]
                                if text and all(32<=b<127 for b in text):row['possible_string']=text.decode()
                            except ValueError:pass
                        except ValueError:pass
                rows.append(row)
        return {'sha256':hashlib.sha256(data).hexdigest(),'start':hex(address),'requested_bytes':size,'mode':'words' if words else 'ARM instructions','decoded_or_read_bytes':len(rows)*4,'rows':rows,'limitation':'Static bytes only; no Thumb decoding, control-flow reachability, vtable ownership or runtime activation inferred.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path);p.add_argument('--start',type=lambda x:int(x,0),required=True);p.add_argument('--bytes',type=lambda x:int(x,0),default=256);p.add_argument('--words',action='store_true');a=p.parse_args()
    try:print(json.dumps(trace(a.elf,a.start,a.bytes,a.words),indent=2))
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
