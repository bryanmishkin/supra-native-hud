#!/usr/bin/env python3
"""Run captured producer resolution-selection code offline, never on a vehicle.

This executes native ARM instructions; external services are intercepted. It
does not emulate a cluster, claim receiver clipping, or authorize live writes.
"""
import argparse
import json
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from verify_pip_binding_records import cpu_for, word, BASE, CTL


def probe(path, selected, selection, dimensions, coding_available=True):
    cpu = cpu_for(path, CTL)
    owner, call, parent, service = [BASE + n for n in (0x1000, 0x2000, 0x3000, 0x4000)]
    cpu.mem_write(owner + 0xe4, bytes([coding_available]))
    word(cpu, owner + 0x114, selected)
    word(cpu, owner + 0x10c, 6)
    word(cpu, owner + 0x110, 4)
    word(cpu, owner + 0x1c, parent)
    word(cpu, parent + 0xa8, service)
    cpu.mem_write(service + 0x50, b'\1')  # maneuver service connected
    for offset, value in zip((0x10, 0x14, 0x18, 0x1c), (*dimensions, selection)):
        word(cpu, call + offset, value)
    cpu.reg_write(UC_ARM_REG_R0, owner)
    cpu.reg_write(UC_ARM_REG_R1, call)
    cpu.reg_write(UC_ARM_REG_LR, BASE)
    reads, events = [], []
    targets = {0x6de010: 'initialize_cluster', 0x6dde60: 'initialize_hud',
               0x6d8818: 'select_style', 0x2dbf24: 'complete',
               0x6d6ec0: 'current_view_type', 0x6dbbc8: 'attach_view',
               0x1286a8: 'log', 0x126f68: 'log'}
    def code(c, address, size, data):
        if address in targets:
            args = [c.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            events.append({'operation': targets[address], 'arguments': args})
            c.reg_write(UC_ARM_REG_R0, 8 if address == 0x6d6ec0 else 1)
            c.reg_write(UC_ARM_REG_PC, c.reg_read(UC_ARM_REG_LR))
        elif not (0x6de214 <= address < 0x6de788 or 0x6d71d8 <= address < 0x6d7590):
            raise RuntimeError('Unreviewed native target ' + hex(address))
    def read(c, access, address, size, value, data):
        if call + 0x10 <= address < call + 0x20:
            reads.append(address - call)
    cpu.hook_add(UC_HOOK_CODE, code)
    cpu.hook_add(UC_HOOK_MEM_READ, read)
    cpu.emu_start(0x6de214, BASE, count=2000)
    assert cpu.reg_read(UC_ARM_REG_PC) == BASE, 'Native function did not return'
    assert set(reads) <= {0x1c}, 'Dimension fields consumed: review conclusion'
    return {'coding_available_fixture': coding_available, 'previous_selection': selected, 'request_selection': selection,
            'request_dimensions': dimensions, 'request_offsets_read': sorted(set(reads)),
            'events': events}


def ethernet_gate(path):
    """Execute actual coding callback/getter; intercept backing coding store only."""
    cpu = cpu_for(path, CTL)
    owner, coding = BASE + 0x1000, BASE + 0x2000
    word(cpu, owner + 0xe8, coding)
    cpu.mem_write(owner + 0xe4, b'\0')
    cpu.reg_write(UC_ARM_REG_R0, owner)
    cpu.reg_write(UC_ARM_REG_LR, BASE)
    writes, queries, calls = [], [], []
    def code(c, address, size, data):
        if address == 0x6f3cd4:
            key = c.reg_read(UC_ARM_REG_R1)
            assert key == 0x48800818
            queries.append(hex(key))
            c.reg_write(UC_ARM_REG_R0, 3)  # explicit Ethernet coding fixture
            c.reg_write(UC_ARM_REG_PC, c.reg_read(UC_ARM_REG_LR))
        elif address in (0x1274b4, 0x31d10c, 0x129200, 0x12914c):
            calls.append(hex(address))  # strings/logging only
            c.reg_write(UC_ARM_REG_R0, 0)
            c.reg_write(UC_ARM_REG_PC, c.reg_read(UC_ARM_REG_LR))
        elif not (0x6ddb74 <= address <= 0x6dde10 or 0x6f453c <= address <= 0x6f45fc):
            raise RuntimeError('Unreviewed coding target ' + hex(address))
    def write(c, access, address, size, value, data):
        if owner <= address < owner + 0x200:
            writes.append({'offset': hex(address-owner), 'size': size, 'value': value})
    cpu.hook_add(UC_HOOK_CODE, code)
    cpu.hook_add(UC_HOOK_MEM_WRITE, write)
    cpu.emu_start(0x6ddb74, BASE, count=2000)
    assert cpu.reg_read(UC_ARM_REG_PC) == BASE
    assert queries == ['0x48800818']
    assert not writes
    assert bytes(cpu.mem_read(owner + 0xe4, 1)) == b'\0'
    rejection = probe(path, 0, 4, (1, 800, 480), coding_available=False)
    assert not [e for e in rejection['events'] if e['operation'] in
                ('initialize_cluster', 'initialize_hud', 'select_style', 'attach_view')]
    return {'coding_value_fixture': 3, 'coding_queries': queries,
            'owner_writes': writes, 'coding_available_remains_false': True,
            'subsequent_resolution_request': rejection,
            'scope': 'Native callback and getter with fixture coding value; not a live coding read'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--controller', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    rows = []
    for selected in (0, 4):
        for selection in (0, 1, 2, 3, 4, 5, 6, 255):
            pair = [probe(a.controller, selected, selection, dims)
                    for dims in ((1, 150, 36), (7, 800, 480))]
            assert pair[0]['events'] == pair[1]['events'], 'Dimensions altered routing'
            rows.extend(pair)
    result = {'binary_sha256': CTL, 'native_handler': '0x6de214',
              'cases': rows, 'case_count': len(rows),
              'scope': 'Head-unit producer handler under explicit service-state fixtures; not cluster firmware',
              'dimension_changes_alter_observed_calls': False,
              'ethernet_gate': ethernet_gate(a.controller),
              'live_test_admitted': False}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'cases': len(rows), 'dimension_changes_alter_observed_calls': False}))


if __name__ == '__main__':
    main()
