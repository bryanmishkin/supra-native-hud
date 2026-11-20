#!/usr/bin/env python3
"""Execute captured HUD adjustment methods offline. No network or vehicle writes.

Intercepts the transport sender to record arguments, then executes its native
serializer control flow with scalar writes recorded (not a wire-byte simulator).
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from verify_pip_binding_records import cpu_for, BASE, word

SHA = 'fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935'
SENDER = 0x230774c
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)


def arguments(cpu):
    return [cpu.reg_read(r) for r in REGS] + list(struct.unpack(
        '<6I', bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_SP), 24))))


def caller(path, start, value, current=0):
    cpu = cpu_for(path, SHA)
    owner, parent = BASE + 0x1000, BASE + 0x2000
    word(cpu, owner + 0x7c, parent)
    word(cpu, owner + 0x8c, current)
    cpu.reg_write(UC_ARM_REG_R0, owner)
    cpu.reg_write(UC_ARM_REG_R1, value & 0xffffffff)
    cpu.reg_write(UC_ARM_REG_LR, BASE)
    calls = []
    def hook(c, address, size, data):
        if address == SENDER:
            calls.append(arguments(c))
            c.reg_write(UC_ARM_REG_R0, 1)
            c.reg_write(UC_ARM_REG_PC, c.reg_read(UC_ARM_REG_LR))
        elif not start <= address < start + 0x70:
            raise RuntimeError('Unexpected native call: ' + hex(address))
    cpu.hook_add(UC_HOOK_CODE, hook)
    cpu.emu_start(start, BASE, count=150)
    assert cpu.reg_read(UC_ARM_REG_PC) == BASE
    for call in calls:
        assert call[0] == parent + 0x25f4
    return calls


def serialize(path, args):
    cpu = cpu_for(path, SHA)
    for reg, value in zip(REGS, args):
        cpu.reg_write(reg, value)
    cpu.mem_write(cpu.reg_read(UC_ARM_REG_SP), struct.pack('<6I', *args[4:]))
    cpu.reg_write(UC_ARM_REG_LR, BASE)
    fields, sends = [], []
    def hook(c, address, size, data):
        if address in (0x2195efc, 0x21963b0):
            value, low, high = [c.reg_read(r) for r in REGS[1:]]
            fields.append(dict(bits=8 if address == 0x2195efc else 32,
                               value=value, minimum=low, maximum=high))
            c.reg_write(UC_ARM_REG_R0, int(low <= value <= high))
        elif address == 0x2191e40:
            sends.append(address)
            c.reg_write(UC_ARM_REG_R0, 1)
        elif address in (0x2195a88, 0x2191ab4, 0x21929c8, 0x25a00e8):
            c.reg_write(UC_ARM_REG_R0, 1)
        elif 0x230774c <= address <= 0x2307948:
            return
        else:
            raise RuntimeError('Unexpected native call: ' + hex(address))
        c.reg_write(UC_ARM_REG_PC, c.reg_read(UC_ARM_REG_LR))
    cpu.hook_add(UC_HOOK_CODE, hook)
    cpu.emu_start(SENDER, BASE, count=500)
    assert cpu.reg_read(UC_ARM_REG_PC) == BASE
    assert len(sends) == 1
    return fields


def verify(path):
    results = []
    # Modes here are synthetic branch inputs, NOT authorization to send them.
    for mode in (0, 1, 6, 7):
        calls = caller(path, 0xf4a6c0, mode, current=(mode + 1) % 8)
        expected = [0, 6, 0, mode, 0, 0x40000000, 255, 255, 255]
        assert len(calls) == 1 and calls[0][1:] == expected
        fields = serialize(path, calls[0])
        assert [f['value'] for f in fields] == expected
        assert [f['maximum'] for f in fields] == [31,7,31,7,31,0xffffffff,255,255,255]
        assert caller(path, 0xf4a6c0, mode, current=mode) == []
        results.append(dict(method='setMode', input=mode, fields=fields,
                            unchanged_mode_sends_nothing=True))
    for start, field in ((0xf4a720,4),(0xf4a788,2),(0xf4a7f0,0)):
        for value in (-10, 0, 10):
            calls = caller(path, start, value)
            expected = [0,6,0,6,0,0x40000000,255,255,255]
            expected[field] = value + 11
            assert len(calls) == 1 and calls[0][1:] == expected
            fields = serialize(path, calls[0])
            assert [f['value'] for f in fields] == expected
            results.append(dict(method=hex(start), input=value, fields=fields))
        for invalid in (-11, 11):
            assert caller(path, start, invalid) == []
    captured = []
    for value, body in ((-1, '00060a060040000000ffffff'),
                        (0, '00060b060040000000ffffff')):
        fields = list(struct.unpack('>5BI3B', bytes.fromhex(body)))
        assert caller(path, 0xf4a788, value)[0][1:] == fields
        captured.append(dict(ui_value=value, captured_body=body,
                             native_scalar_match=True))
    return dict(binary_sha256=SHA, cases=results, vehicle_contact=False,
                captured_height_matches=captured,
                invalid_adjustments_rejected=6,
                limitation='Executed sender/caller control flow only. Scalar transport, initialization, cache invalidation and send/destructor calls intercepted. No receiver execution, physical viewport, mode semantics, or raw wire encoding proved. No live control command generated.')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('hmi', type=Path)
    print(json.dumps(verify(p.parse_args().hmi), indent=2))
