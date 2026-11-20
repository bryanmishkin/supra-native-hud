#!/usr/bin/env python3
"""Execute captured NavigationBasic's existing-window rectangle setter offline."""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                              UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
from verify_pip_binding_records import cpu_for, BASE, word
BASIC = 'd03464928749857ceab8daec20db422cf81d47f722ae4bb9d9c54a03057c1206'

def verify(path):
    results = []
    for name, old, new, dirty in [
        ('translated_non_square', (0, 0, 800, 480), (37, 53, 277, 160), 0),
        ('unchanged', (37, 53, 277, 160), (37, 53, 277, 160), 0),
        ('already_dirty', (37, 53, 277, 160), (91, 27, 460, 237), 1),
    ]:
        cpu = cpu_for(path, BASIC)
        obj = BASE + 0x1000
        original = bytearray(b'\xa5' * 0x80)
        x, y, width, height = old
        struct.pack_into('<IIII', original, 0x18, width, height, x, y)
        struct.pack_into('<I', original, 0x34, 1)  # existing synthetic surface handle
        original[0x38] = dirty
        cpu.mem_write(obj, bytes(original))
        for reg, val in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), (obj, *new[:3])):
            cpu.reg_write(reg, val)
        word(cpu, cpu.reg_read(UC_ARM_REG_SP), new[3])
        cpu.reg_write(UC_ARM_REG_LR, BASE)
        executed = []
        def trace(uc, address, size, data):
            if not 0xdbb224 <= address <= 0xdbb2b8:
                raise AssertionError(f'Unexpected external instruction {address:#x}')
            executed.append(address)
        cpu.hook_add(UC_HOOK_CODE, trace)
        cpu.emu_start(0xdbb224, BASE, count=100)
        assert cpu.reg_read(UC_ARM_REG_PC) == BASE
        actual = bytes(cpu.mem_read(obj, len(original)))
        expected = bytearray(original)
        x, y, width, height = new
        struct.pack_into('<IIII', expected, 0x18, width, height, x, y)
        expected[0x38] = int(bool(dirty or old != new))
        assert actual == bytes(expected), 'Unexpected rectangle or adjacent memory change'
        results.append(dict(name=name, before_xywh=old, after_xywh=new,
                            dirty_before=dirty, dirty_after=actual[0x38],
                            instructions=len(executed), adjacent_guards_unchanged=True,
                            external_callbacks=0))
    return dict(binary_sha256=BASIC, entry='0xdbb224', cases=results,
                vehicle_contact=False,
                limitation='Existing NGraphicsSystem::CWindow local rectangle storage only. Synthetic inputs do not prove receiver routing, HUD bounds, or valid physical screen sizes.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('navigation_basic', type=Path)
    print(json.dumps(verify(parser.parse_args().navigation_basic), indent=2))
