#!/usr/bin/env python3
"""Offline ARM ELF import-call inventory, including literal linker veneers.

Requires pyelftools and capstone. Does not execute or alter the input ELF.
Linear disassembly is evidence for review, not proof of reachable control flow.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from elftools.elf.elffile import ELFFile


def trace_imports(path, start, size):
    if size <= 0 or size > 65536 or start % 4 or size % 4:
        raise ValueError('Use an aligned ARM region of 4..65536 bytes')
    data = path.read_bytes()
    with path.open('rb') as stream:
        elf = ELFFile(stream)
        if elf['e_machine'] != 'EM_ARM' or not elf.little_endian:
            raise ValueError('Expected little-endian ARM ELF')
        segments = [(s['p_vaddr'], s['p_offset'], s['p_filesz'])
                    for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
        plt = elf.get_section_by_name('.plt')
        rel = elf.get_section_by_name('.rel.plt')
        symbols = elf.get_section_by_name('.dynsym')
        if not plt or not rel or not symbols:
            raise ValueError('Required ARM PLT/relocation sections absent')
        relocations = list(rel.iter_relocations())
        if plt['sh_size'] != 20 + 12 * len(relocations):
            raise ValueError('Unsupported PLT layout; do not guess import addresses')
        imports = {plt['sh_addr'] + 20 + 12*i:
                   symbols.get_symbol(r['r_info_sym']).name
                   for i, r in enumerate(relocations)}
    def read(address, count):
        for va, offset, length in segments:
            if va <= address and address + count <= va + length:
                return data[offset + address-va:offset + address-va + count]
        return b''
    if len(read(start, size)) != size:
        raise ValueError('Region must lie inside one file-backed LOAD segment')
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    calls = []
    for address in range(start, start + size, 4):
        for ins in decoder.disasm(read(address, 4), address):
            if ins.mnemonic not in ('b', 'bl') or not ins.op_str.startswith('#0x'):
                continue
            target = int(ins.op_str[1:], 16)
            direct = target
            raw = read(target, 8)
            # ARM ldr pc,[pc,#-4]: absolute target in following literal word.
            if len(raw) == 8 and struct.unpack('<I', raw[:4])[0] == 0xe51ff004:
                target = struct.unpack('<I', raw[4:])[0]
            if target in imports:
                calls.append(dict(address=hex(address), branch_target=hex(direct),
                                  import_address=hex(target), symbol=imports[target]))
    return dict(sha256=hashlib.sha256(data).hexdigest(), start=hex(start),
                size=size, calls=calls, reachable_control_flow_proven=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('--start', required=True, type=lambda s: int(s, 0))
    parser.add_argument('--size', required=True, type=lambda s: int(s, 0))
    args = parser.parse_args()
    print(json.dumps(trace_imports(args.elf, args.start, args.size), indent=2))
