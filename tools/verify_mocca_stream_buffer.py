#!/usr/bin/env python3
"""Run captured MOCCA buffered writes offline. No connection or receiver simulation."""
import argparse
import json
from pathlib import Path
from verify_pip_binding_records import cpu_for, word, BASE
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR

SHA = '140ee2e9816b91b58f6b0d81df6a609e533035892710c54c4e520147a548ff15'


def verify(path):
    results = []
    for payload in [bytes.fromhex('000000006d200003'), bytes.fromhex('feffffffd2200003'), bytes(range(256))]:
        cpu = cpu_for(path, SHA)
        owner, buffer, source = BASE + 0x1000, BASE + 0x2000, BASE + 0x3000
        cpu.mem_write(source, payload)
        for offset, value in [(0x18, 1024), (0x48, buffer), (0x50, 40), (0x14, 1064)]:
            word(cpu, owner + offset, value)
        calls = []
        def boundary(c, address, size, user):
            if address == 0x5e97c:  # resolved memcpy import
                destination = c.reg_read(UC_ARM_REG_R0)
                src, count = c.reg_read(UC_ARM_REG_R1), c.reg_read(UC_ARM_REG_R2)
                assert destination == buffer and src == source and count == len(payload)
                c.mem_write(destination, bytes(c.mem_read(src, count)))
                calls.append(count)
                c.reg_write(UC_ARM_REG_PC, c.reg_read(UC_ARM_REG_LR))
        cpu.hook_add(UC_HOOK_CODE, boundary)
        for register, value in [(UC_ARM_REG_R0, owner), (UC_ARM_REG_R1, source),
                                (UC_ARM_REG_R2, len(payload)), (UC_ARM_REG_LR, BASE)]:
            cpu.reg_write(register, value)
        cpu.emu_start(0x9d95c, BASE, count=500)
        assert cpu.reg_read(UC_ARM_REG_PC) == BASE
        assert cpu.reg_read(UC_ARM_REG_R0) == len(payload)
        assert bytes(cpu.mem_read(buffer, len(payload))) == payload
        results.append({'input_hex': payload.hex(), 'output_identical': True, 'memcpy_sizes': calls})
    return {'sha256': SHA, 'entry': '0x9d95c', 'cases': results,
            'boundary': 'Actual doWrite buffered branch; memcpy implemented at import boundary. No flush, connection bootstrap, framing acceptance, or receiver execution.',
            'vehicle_contact': False, 'receiver_acceptance_proven': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library', type=Path)
    print(json.dumps(verify(parser.parse_args().library), indent=2))
