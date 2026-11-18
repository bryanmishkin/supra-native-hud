#!/usr/bin/env python3
"""Execute bounded, non-I/O ARM driver routines offline. Never connects to a car.
Requires pyelftools and Unicorn; exact captured ELF hashes are mandatory.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC

# Filled from verified captures; no OEM bytes are shipped with this tool.
HASHES={'config': 'e244a9cf9285abe50f1856056ef51a0be39cda3ddaf2f60493ff4ec87d9041b4', 'driver': '36250e84e7fee61f0b1e793c1f95afeb642eddedc8bc9f0dd38a8e8572a30239'}

def inspect(path,expected,kind):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Reference ELF hash mismatch')
    uc=Uc(UC_ARCH_ARM,UC_MODE_ARM);uc.mem_map(0,0x200000)
    uc.mem_map(0x300000,0x100000)
    with path.open('rb') as f:
        e=ELFFile(f)
        if e['e_machine']!='EM_ARM' or not e.little_endian or e.elfclass!=32:raise ValueError('Unsupported ELF')
        for seg in e.iter_segments():
            if seg['p_type']=='PT_LOAD':uc.mem_write(seg['p_vaddr'],seg.data())
        syms=list(e.get_section_by_name('.dynsym').iter_symbols());byname={s.name:s for s in syms}
        rel=e.get_section_by_name('.rel.dyn')
        if rel:
            for r in rel.iter_relocations():
                typ=r['r_info_type'];addr=r['r_offset'];sym=syms[r['r_info_sym']]
                old=struct.unpack('<I',uc.mem_read(addr,4))[0]
                if typ==23:continue # load base is zero
                if typ in (2,21) and sym['st_shndx']!='SHN_UNDEF':
                    val=sym['st_value']+(old if typ==2 else 0)
                    uc.mem_write(addr,struct.pack('<I',val))
        plt=e.get_section_by_name('.plt');rel=e.get_section_by_name('.rel.plt')
        imports={plt['sh_addr']+20+12*i:syms[r['r_info_sym']].name for i,r in enumerate(rel.iter_relocations())}
    heap=[0x310000];calls=[];mode_calls=[]
    def hook(machine,address,size,user):
        if address not in imports:return
        name=imports[address];calls.append(name)
        if name=='malloc':
            size=machine.reg_read(UC_ARM_REG_R0)
            if not 0<size<=4096:raise ValueError('Unexpected allocation')
            result=heap[0];heap[0]+=4096
        elif name=='free':result=0
        elif name=='tda19988_set_mode':
            mode_calls.append(list(struct.unpack('<7I',machine.mem_read(machine.reg_read(UC_ARM_REG_R0),28))));result=0
        else:raise ValueError('Unexpected external call: '+name)
        machine.reg_write(UC_ARM_REG_R0,result);machine.reg_write(UC_ARM_REG_PC,machine.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE,hook)
    def call(name,args):
        for reg,val in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):uc.reg_write(reg,val)
        uc.reg_write(UC_ARM_REG_SP,0x3f0000);uc.reg_write(UC_ARM_REG_LR,0x3ff000)
        uc.emu_start(byname[name]['st_value'],0x3ff000,count=2000)
        if uc.reg_read(UC_ARM_REG_PC)!=0x3ff000:raise ValueError('Instruction budget exhausted')
        return uc.reg_read(UC_ARM_REG_R0)
    def word(a):return struct.unpack('<I',uc.mem_read(a,4))[0]
    def text(a):
        if not a:return None
        return bytes(uc.mem_read(a,64)).split(b'\0',1)[0].decode('ascii')
    result={'sha256':expected,'hardware_or_network_calls':False,'emulation_boundary':'malloc/free handled locally; tda19988_set_mode intercepted to record arguments, never executed'}
    if kind=='config':
        ports=[]
        for ident in (0,1,2,3,99):
            uc.mem_write(0x300000,b'\0'*4)
            rc=call('wfdcfg_port_create',[0x300000,0x300100,ident,0]);entry={'id':ident,'return_code':rc,'extensions':[]}
            if rc==0:
                obj=word(0x300000);table=word(obj+4)
                for off in range(0,120,12):
                    name=word(table+off)
                    if not name:break
                    entry['extensions'].append({'name':text(name),'value':word(table+off+4),'callback':hex(word(table+off+8))})
                else:raise ValueError('Unterminated extension table')
            ports.append(entry)
        assert [p['id'] for p in ports if p['return_code']==0]==[1,2]
        assert ports[2]['extensions']==[{'name':'port_init1','value':0,'callback':'0x2b34'},{'name':'port_uninit1','value':0,'callback':'0x2a74'},{'name':'port_set_mode2','value':0,'callback':'0x29b0'},{'name':'enable_rgba_over_rgb','value':1,'callback':'0x0'}]
        result['ports']=ports
        conversions=[]
        for enabled in (0,1):
            uc.mem_write(byname['enable_rgba_rgb_conversion']['st_value'],struct.pack('<I',enabled))
            for width in (150,320,640,800,1280,1440,1600,1920):
                values=[40000,width,480,0x01020304,0x05060708,0x090a0b0c,0]
                uc.mem_write(0x300200,struct.pack('<7I',*values))
                call('port_set_mode2',[0,0x300200,0,0])
                actual=mode_calls[-1];padded=width
                while padded%3:padded+=32
                expected_width=padded*4//3 if enabled else width
                assert actual[1]==expected_width and actual[:1]+actual[2:]==values[:1]+values[2:]
                conversions.append({'conversion_enabled':bool(enabled),'input_width':width,'transmitter_width':actual[1]})
        result['mode_conversions']=conversions
    else:
        values=[call('wfdCreateSourceFromStream',args) for args in ((0,0,0,0),(1,2,3,4),(0xffffffff,)*4)]
        assert values==[0,0,0] and not calls
        result['stream_source_results']=values
    result['external_calls']=calls
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--driver',type=Path,required=True);a=p.parse_args()
    print(json.dumps({'configuration':inspect(a.config,HASHES['config'],'config'),'output_driver':inspect(a.driver,HASHES['driver'],'driver'),'larger_windshield_test_ready':False},indent=2))
if __name__=='__main__':main()
