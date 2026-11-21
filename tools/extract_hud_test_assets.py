#!/usr/bin/env python3
"""Resolve actual packaged HUD bitmap names with native receiver tree search.
Writes proprietary reference images only to the explicitly supplied private output.
"""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from verify_hud_uploaded_image_path import SHA

def extract(image,package,out):
    code=image.read_bytes();b=package.read_bytes()
    assert hashlib.sha256(code).hexdigest()==SHA
    assert hashlib.sha256(b).hexdigest()=='0d0814d2851a013504bd39e5258c27e8a4584fcfc36f5218b050b1da1aa687b2'
    assert b[:4]==bytes.fromhex('ce510000')
    length=struct.unpack_from('<I',b,4)[0];assert length<=len(b)
    assert struct.unpack_from('<I',b,0x7c)[0]==26
    # Layout independently follows native parser 313078,313340,31341c.
    strings=struct.unpack_from('<I',b,0x58)[0]
    kind,table,base,_=struct.unpack_from('<4I',b,0x80+3*16);assert kind==7
    _,count,_=struct.unpack_from('<3I',b,table)
    records=[struct.unpack_from('<5I',b,table+12+i*20) for i in range(count)]
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    u.mem_map(0x10000,(len(code)+4095)&~4095);u.mem_write(0x10000,code)
    u.mem_map(0x3000000,0x200000)
    obj,nodes,names,arg=0x3001000,0x3010000,0x3080000,0x3100000
    def word(a,v):u.mem_write(a,struct.pack('<I',v))
    word(obj+3*40+4,nodes)
    ns=[];cursor=names
    for i,(name,left,right,offset,size) in enumerate(records):
        p=strings+name+2;end=b.index(b'\0',p);s=b[p:end]
        assert end<strings+8+struct.unpack_from('<I',b,strings)[0]
        ns.append(s);u.mem_write(cursor,s+b'\0')
        children=[]
        for child in (left,right):
            if child==0xffffffff:children.append(0)
            else:
                assert child>=12 and (child-12)%20==0 and (child-12)//20<count
                children.append(nodes+child-12)
        u.mem_write(nodes+20*i,struct.pack('<5I',cursor,*children,offset,size));cursor+=len(s)+1
    found=[]
    for i,name in enumerate(ns):
        if not name.startswith(b'Imports#hud#hud_TestBmp#'):continue
        u.mem_write(arg,name+b'\0');u.reg_write(UC_ARM_REG_SP,0x31ff000)
        u.reg_write(UC_ARM_REG_LR,0x31ffff0)
        for r,v in [(UC_ARM_REG_R0,obj),(UC_ARM_REG_R1,3),(UC_ARM_REG_R2,arg)]:u.reg_write(r,v)
        # Stop after native strcmp/tree branch selects the exact record, before I/O.
        u.emu_start(0x31394c,0x313a28,count=100000)
        assert u.reg_read(UC_ARM_REG_PC)==0x313a28
        assert u.reg_read(UC_ARM_REG_R5)==nodes+20*i
        offset=base+records[i][3];stored,typ,key=struct.unpack_from('<III',b,offset)
        assert typ==7
        assert key==records[i][0], 'Payload header key must equal native tree key'
        dec=zlib.decompressobj();raw=dec.decompress(b[offset+12:offset+stored]);raw+=dec.flush();assert dec.eof
        header=struct.unpack_from('<9I',raw);w,h=header[1:3];assert (w,h)==(408,132)
        assert len(raw)==36+w*h*4 and header[-1]==w*h*4
        filename=name.decode().split('#')[-1]+'.png'
        def chunk(kind,data):
            return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
        pixels=raw[36:];scan=b''.join(b'\0'+pixels[y*w*4:(y+1)*w*4] for y in range(h))
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b'')
        (out/filename).write_bytes(png)
        found.append(dict(name=name.decode(),record_index=i,record_offset=hex(table+12+i*20),payload_offset=hex(offset),width=w,height=h,rgba_sha256=hashlib.sha256(raw[36:]).hexdigest(),reference_png=filename,native_name_search=True))
    assert len(found)==26
    return dict(passed=True,image_sha256=SHA,package_sha256=hashlib.sha256(b).hexdigest(),native_tree_search_entry='0x31394c',native_stop_before_stream_access='0x313a28',assets=found,
      limits='Real packaged tree names and child offsets relocated into synthetic nodes according to native parser. Native search/strcmp selects each exact record with no stubs. Python zlib decompression, not native asset construction/rendering. Images remain private. No arbitrary upload, scene mutation or installed008 execution.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    r=extract(a.image,a.package,a.output);(a.output/'asset-reference-manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS: 26 exact package-to-name associations through native tree search; private reference PNGs saved')
