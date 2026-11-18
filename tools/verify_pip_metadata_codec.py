#!/usr/bin/env python3
"""Compare codec with captured ARM instructions using Unicorn, entirely offline.

Requires unicorn and pyelftools. Reads the owner's retained NavigationFully;
no factory bytes are distributed with this tool. Only the bounded byte-rotation
block executes, with its memcpy dependency handled at the ABI boundary.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_LR
from unicorn.arm_const import UC_ARM_REG_PC
from pip_metadata_strip import encode_record, decode_upload

EXPECTED = '957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d'
START, STOP, COPY = 0x87c03c, 0x87c068, 0x105d20


def verify(path):
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != EXPECTED:
        raise ValueError('NavigationFully identity differs; refusing fixed-address trace')
    with path.open('rb') as f:
        elf = ELFFile(f)
        code = None
        for seg in elf.iter_segments():
            a, n = seg['p_vaddr'], seg['p_filesz']
            if seg['p_type'] == 'PT_LOAD' and a <= START < STOP <= a+n:
                o = seg['p_offset'] + START-a
                code = data[o:o+STOP-START]
        if code is None:
            raise ValueError('Trace is not in a file-backed load segment')
    cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    cpu.mem_map(START & ~4095, 4096)
    cpu.mem_map(COPY & ~4095, 4096)
    cpu.mem_map(0x20000000, 4096)
    cpu.mem_write(START, code)
    def memcpy_boundary(uc, address, size, user):
        if address == COPY:
            dst, src, count = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
            if count != 83 or dst != 0x20000800 or src != 0x20000115:
                raise AssertionError('Unexpected memcpy arguments')
            uc.mem_write(dst, bytes(uc.mem_read(src, count)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    cpu.hook_add(UC_HOOK_CODE, memcpy_boundary)
    rng = random.Random(0x504950)
    vectors = [bytes(84), bytes([255])*84, bytes(range(84))]
    vectors += [bytes(rng.randrange(256) for _ in range(84)) for _ in range(256)]
    for record in vectors:
        cpu.mem_write(0x20000114, record)
        cpu.mem_write(0x20000800, bytes([0xa5])*84)
        cpu.reg_write(UC_ARM_REG_R4, 0x20000100)
        cpu.reg_write(UC_ARM_REG_R5, 0x20000800)
        cpu.reg_write(UC_ARM_REG_R6, 0x20000114)
        cpu.emu_start(START, STOP, count=1000)
        if cpu.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('Bounded trace did not finish')
        observed = bytes(cpu.mem_read(0x20000800, 84))
        if observed != encode_record(record) or decode_upload(observed) != record:
            raise AssertionError('Codec differs from captured instructions')
    return {'binary_sha256': actual, 'instruction_sha256': hashlib.sha256(code).hexdigest(),
            'start': hex(START), 'stop': hex(STOP), 'matching_vectors': len(vectors),
            'memcpy_dependency': 'ABI-boundary copy, 83 bytes', 'vehicle_contact': False,
            'windshield_delivery_proven': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('navigation_fully', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.navigation_fully), indent=2))
