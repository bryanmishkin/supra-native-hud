#!/usr/bin/env python3
"""Offline receiver column dispatch and packaged HUD image rectangles; no car I/O."""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R5, UC_ARM_REG_PC
from verify_hud_uploaded_image_path import SHA
SCENE_SHA = '1d3fc97687f40571348761cd5ea33d41875aa11177456522693d786c8e1eda72'

def verify(image, scene):
    code, data = image.read_bytes(), scene.read_bytes()
    assert hashlib.sha256(code).hexdigest() == SHA
    assert hashlib.sha256(data).hexdigest() == SCENE_SHA
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x10000, (len(code)+4095)&~4095)
    u.mem_write(0x10000, code)
    routes=[]
    for column in range(5):
        u.reg_write(UC_ARM_REG_R5, column)
        # Only native branch selection; stop before argument loads/calls.
        u.emu_start(0x2b059f, 0, count=3 if column else 1)
        pc=u.reg_read(UC_ARM_REG_PC)
        assert pc == (0x2b05a4 if column in (0,4) else 0x2b05ae)
        routes.append(dict(column=column,route='bitmap' if column in (0,4) else 'text',pc=hex(pc)))
    rectangles=[]
    for widget, offsets in [('KITable2DHud',[0x4ff0,0x50f4,0x51f8]),('KIListHud2D',[0x7e6c,0x7f70,0x8074])]:
        for row, off in enumerate(offsets):
            x,y=struct.unpack_from('<2f',data,off+12)
            w,h=struct.unpack_from('<2f',data,off+48)
            assert (x,y,w,h)==(158.,[35.,67.,101.][row],28.,28.)
            rectangles.append(dict(widget=widget,row=row+1,record_offset=hex(off),xywh=[x,y,w,h]))
    return dict(passed=True,image_sha256=SHA,scene_sha256=SCENE_SHA,columns=routes,rectangles=rectangles,
        limits='Native column branch only, no copy/render calls executed. Packaged rectangles are not measured physical clipping or proof of active parent visibility. Three separated 28x28 icons do not form a 408x132 uploaded canvas. No live test admitted from this alone.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('image','scene','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=verify(a.image,a.scene);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print('PASS: five native column branches and six HUD image rectangles')
