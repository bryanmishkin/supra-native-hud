#!/usr/bin/env python3
"""Execute the captured tag-5 control writer offline; never contacts a vehicle."""
import argparse
import json
import struct
from pathlib import Path
from verify_pip_binding_records import (
    BASE, CTL, cpu_for, word, UC_HOOK_CODE, UC_ARM_REG_R0,
    UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC,
)


def verify(path):
    cpu = cpu_for(path, CTL)
    obj, stream, buf = BASE + 0x1000, BASE + 0x2000, BASE + 0x4000
    imports = set()

    def boundary(uc, address, size, user):
        if address == 0x127508:
            dst = uc.reg_read(UC_ARM_REG_R0)
            uc.mem_write(dst, struct.pack('<II', uc.reg_read(UC_ARM_REG_R1),
                                          uc.reg_read(UC_ARM_REG_R2)))
            imports.add('stream snapshot')
        elif address == 0x12a604:
            st, src, length = [uc.reg_read(r) for r in
                              (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
            assert length in (1, 2, 4)
            cur = struct.unpack('<I', uc.mem_read(st + 4, 4))[0]
            assert buf <= cur and cur + length <= buf + 64
            uc.mem_write(cur, bytes(uc.mem_read(src, length)))
            word(uc, st + 4, cur + length)
            uc.reg_write(UC_ARM_REG_R0, length)
            imports.add('stream write')
        else:
            return
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    cpu.hook_add(UC_HOOK_CODE, boundary)
    rows = []
    for target in range(4):
        for content in range(4):
            # Native tuple: model identity/type, render instance, referred
            # maneuver, target enum, content enum. Values are synthetic.
            cpu.mem_write(obj, struct.pack('<IIIIII', 0x32000001, 50,
                                          0x12345678, 0xabcdef01, target, content))
            word(cpu, stream, buf)
            word(cpu, stream + 4, buf)
            cpu.reg_write(UC_ARM_REG_R0, stream)
            cpu.reg_write(UC_ARM_REG_R1, obj)
            cpu.reg_write(UC_ARM_REG_LR, BASE)
            cpu.emu_start(0xbb0aac, BASE, count=4000)
            assert cpu.reg_read(UC_ARM_REG_PC) == BASE
            end = struct.unpack('<I', cpu.mem_read(stream + 4, 4))[0]
            actual = bytes(cpu.mem_read(buf, end - buf))
            expected = struct.pack('>IBIIBB', 0x32000001, 50,
                                   0x12345678, 0xabcdef01, target, content)
            assert actual == expected
            rows.append({'target': target, 'content': content,
                         'payload': actual.hex()})
    return {'binary_sha256': CTL, 'entry': '0xbb0aac', 'cases': rows,
            'imports_supplied': sorted(imports), 'payload_bytes': 15,
            'vehicle_contact': False,
            'scope': 'Native sender encoding only. Enum destination meanings, '
                     'receiver support, ownership, and visibility are not proven. '
                     'No x/y/width/height or pixel bytes occur in this tuple.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('controller', type=Path)
    print(json.dumps(verify(parser.parse_args().controller), indent=2))
