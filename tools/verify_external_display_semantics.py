#!/usr/bin/env python3
"""Check captured HMI candidate fields; no vehicle access or receiver simulation."""
import argparse
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_PC
from verify_pip_binding_records import cpu_for, BASE

HMI = 'fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935'


def verify(path):
    cpu = cpu_for(path, HMI)
    getter_cases = []
    for offset, start in [(0x78, 0x2305f1c), (0x7a, 0x2305ee0), (0x7c, 0x2305ea4)]:
        obj, out = BASE + 0x1000, BASE + 0x2000
        cpu.mem_write(obj, bytes(0x100))
        cpu.mem_write(obj + offset, struct.pack('<H', 317))
        cpu.mem_write(out, bytes([0xa5]) * 4)
        cpu.reg_write(UC_ARM_REG_R4, obj)
        cpu.reg_write(UC_ARM_REG_R5, out)
        cpu.emu_start(start, start + 12, count=3)
        assert cpu.reg_read(UC_ARM_REG_PC) == start + 12
        assert bytes(cpu.mem_read(out, 4)) == struct.pack('<H', 317) + b'\xa5\xa5'
        getter_cases.append(dict(offset=hex(offset), start=hex(start), copied_u16=317))
    temperature = []
    for raw in [0, 1, 78, 80, 81, 100, 150, 416]:
        cpu.reg_write(UC_ARM_REG_R2, raw)
        cpu.emu_start(0xf35818, 0xf35834, count=7)
        assert cpu.reg_read(UC_ARM_REG_PC) == 0xf35834
        whole = cpu.reg_read(UC_ARM_REG_R2)
        whole = whole - (1 << 32) if whole & (1 << 31) else whole
        fraction = cpu.reg_read(UC_ARM_REG_R3)
        assert whole == int((raw - 80) / 2)
        assert fraction == (raw & 1) * 5
        fmt_addr = cpu.reg_read(UC_ARM_REG_R1)
        assert bytes(cpu.mem_read(fmt_addr, 6)) == b'%d.%d\0'
        temperature.append(dict(raw=raw, integer_argument=whole, fractional_argument=fraction))
    assert bytes(cpu.mem_read(0x2e8a928, 5)) == b'-0.5\0'
    return dict(binary_sha256=HMI, getter_cases=getter_cases, temperature_arithmetic=temperature,
                special_raw_79_string='-0.5', intercepted_calls=0,
                scope='Getter tails after validity guard; formatting arithmetic before string library call. '
                      'Caller/class identification is a separate static trace; not a complete consumer or receiver emulator.',
                viewport_dimensions_proven=False, larger_windshield_test_ready=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('hmi', type=Path)
    print(json.dumps(verify(p.parse_args().hmi), indent=2))
