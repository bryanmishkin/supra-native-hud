#!/usr/bin/env python3
"""Offline native imgview lookup; extracts private built-in HUD references.
No vehicle access. Requires owner's hash-pinned receiver004 main/data images.
"""
import argparse, hashlib, json, struct, zlib
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0
from verify_hud_uploaded_image_path import SHA
DATA_SHA='b33107cd3bc2b8133bea9b5636add414ce1a45aa6a43bc8b380a830fd7d92a58'

def verify(main,data,out):
    b=main.read_bytes();d=data.read_bytes()
    assert hashlib.sha256(b).hexdigest()==SHA
    assert hashlib.sha256(d).hexdigest()==DATA_SHA
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
    for base,size,content in [(0x10000,(len(b)+4095)&~4095,b),(0xc50000,0x200000,d),(0x3000000,0x10000,b'')]:
        u.mem_map(base,size)
        if content:u.mem_write(base,content)
    stop=0x300fff0;arg=0x3001000;cases=[];assets=[]
    def call(value):
        if value is not None:u.mem_write(arg,value+b'\0')
        u.reg_write(UC_ARM_REG_SP,0x300f000);u.reg_write(UC_ARM_REG_LR,stop|1)
        u.reg_write(UC_ARM_REG_R0,0 if value is None else arg)
        u.emu_start(0x155ed1,stop,count=500000)
        assert u.reg_read(UC_ARM_REG_PC)==stop
        return u.reg_read(UC_ARM_REG_R0)
    assert b[0x492d10-65536]==45
    for i in range(45):
        nameptr=struct.unpack_from('<I',d,0x1fbac+i*4)[0]
        record=struct.unpack_from('<I',d,0x1fc60+i*4)[0]
        name=b[nameptr-65536:b.index(b'\0',nameptr-65536)]
        w,h,n,p=struct.unpack_from('<HHII',b,record-65536)
        for prefix in [b'',b'/not/a/real/file/',b'C:\\not-a-file\\']:
            assert call(prefix+name)==record
            cases.append(dict(argument=(prefix+name).decode(),record=hex(record)))
        row=dict(name=name.decode(),width=w,height=h,compressed_length=n,record=hex(record))
        if (w,h)==(480,240):
            raw=zlib.decompress(b[p-65536:p-65536+n]);assert len(raw)==w*h*4
            output=out/(name.decode()+'.raw');output.write_bytes(raw)
            row.update(raw_file=output.name,raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw))
        assets.append(row)
    for value in [None,b'',b'408x132_marker',b'/tmp/408x132_marker.png',b'0x01000008',b'480x240_TestHUD_text.png',b'480x240_TestHUD_text/']:
        assert call(value)==0;cases.append(dict(argument=None if value is None else value.decode(),record=None))
    return dict(passed=True,cases=cases,assets=assets,image_sha256=SHA,data_sha256=DATA_SHA,
        native_entry='0x155ed0',intercepts=0,
        scope='All 45 native name-table entries, path basename behavior and seven missing inputs. Real native strcmp, no stubs. Extracted two built-in HUD zlib buffers; pixel byte order not asserted. No renderer, command transport or installed008 execution. A filename in imgview is a built-in table key, not filesystem access.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True);r=verify(a.image,a.data,a.output)
    (a.output/'builtin-image-lookup.json').write_text(json.dumps(r,indent=2)+'\n')
    print('PASS:',len(r['cases']),'native lookup cases; two private 480x240 reference buffers')
