#!/usr/bin/env python3
"""Execute bounded factory metadata/ID-selection blocks offline; not a receiver simulator."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

NAV = '957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d'
CTL = '71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a'
BASE = 0x30000000

def cpu_for(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Captured binary hash mismatch; fixed addresses refused')
    cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    with path.open('rb') as f:
        segments = [s for s in ELFFile(f).iter_segments() if s['p_type'] == 'PT_LOAD']
        low = min(s['p_vaddr'] for s in segments) & ~4095
        high = (max(s['p_vaddr'] + s['p_memsz'] for s in segments) + 4095) & ~4095
        if high - low > 128 * 1024 * 1024:
            raise ValueError('Unexpected image span')
        cpu.mem_map(low, high - low)
        for s in segments:
            cpu.mem_write(s['p_vaddr'], s.data())
    cpu.mem_map(BASE, 0x10000)
    cpu.reg_write(UC_ARM_REG_SP, BASE + 0xf000)
    return cpu

def word(cpu, address, value):
    cpu.mem_write(address, struct.pack('<I', value))

def verify(nav, controller):
    cpu = cpu_for(nav, NAV)
    record = BASE + 0x100
    cpu.mem_write(record - 4, bytes([0xa5]) * 92)
    cpu.reg_write(UC_ARM_REG_R0, record)
    cpu.reg_write(UC_ARM_REG_LR, BASE)
    cpu.emu_start(0x87ba68, BASE, count=1000)
    assert cpu.reg_read(UC_ARM_REG_PC) == BASE
    assert bytes(cpu.mem_read(record, 84)) == bytes(84)
    assert bytes(cpu.mem_read(record - 4, 4)) == bytes([0xa5])*4
    assert bytes(cpu.mem_read(record + 84, 4)) == bytes([0xa5])*4
    writes = []
    for start, reg in [(0x7ee598, UC_ARM_REG_R7), (0x7f6464, UC_ARM_REG_R6)]:
        for identity in [0x0f000000, 0x0f000004, 0x12345678]:
            cpu.mem_write(record, bytes(84))
            cpu.reg_write(UC_ARM_REG_SP, record - 0x10)
            cpu.reg_write(reg, BASE + 0x1000)
            word(cpu, BASE + 0x1200, identity)
            cpu.emu_start(start, start + 8, count=2)
            observed = bytes(cpu.mem_read(record, 84))
            expected = bytearray(84)
            struct.pack_into('<I', expected, 16, identity)
            assert observed == bytes(expected)
            writes.append({'start': hex(start), 'identity': hex(identity), 'record_offset': 16})
    selections = []
    for mode, start, stop in [(1, 0xa8ea20, 0xa8eaa0), (0, 0xa8eaa0, 0xa8eb20)]:
        for identity in [0x0f000004, 0xffffffff]:
            cpu = cpu_for(controller, CTL)
            owner, model, stack = BASE + 0x1000, BASE + 0x2000, BASE + 0xf000
            for reg, value in [(UC_ARM_REG_R4, owner), (UC_ARM_REG_R5, model),
                               (UC_ARM_REG_R6, 42), (UC_ARM_REG_R9, 0xffffffff),
                               (UC_ARM_REG_SP, stack)]:
                cpu.reg_write(reg, value)
            word(cpu, owner + 0x15c, mode)
            word(cpu, model + (0xc if mode == 1 else 0x10), identity)
            word(cpu, stack + 0x58, BASE + 0x3000)  # logging flag clear
            calls = []
            def observe(uc, address, size, user):
                if address == 0xa86d30:
                    calls.append(list(struct.unpack('<III', bytes(uc.mem_read(owner + 0x254, 12)))))
                    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            cpu.hook_add(UC_HOOK_CODE, observe)
            cpu.emu_start(start, stop, count=100)
            assert cpu.reg_read(UC_ARM_REG_PC) == stop
            expected = [] if identity == 0xffffffff else [[42, identity, 0xffffffff] if mode == 1 else [42, 0xffffffff, identity]]
            assert calls == expected
            selections.append({'mode': mode, 'identity': hex(identity), 'notification_triplets': calls})
    return {'metadata_binary_sha256': NAV, 'controller_binary_sha256': CTL,
            'initializer_zeroes_exactly_84_bytes': True, 'fixed_offset_writes': writes,
            'id_selections': selections, 'notification_boundary': 'observed arguments; downstream callback skipped',
            'vehicle_contact': False, 'receiver_acceptance_proven': False,
            'limitation': 'Bounded producer blocks only. No cluster receiver firmware, physical transport, or active session simulated.'}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('navigation_fully', type=Path)
    p.add_argument('controller', type=Path)
    a = p.parse_args()
    print(json.dumps(verify(a.navigation_fully, a.controller), indent=2))
