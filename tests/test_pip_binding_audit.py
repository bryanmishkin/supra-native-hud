import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_pip_binding import binding
from pip_trial import descriptor, detail


def frame(method,body,kind=0):
    return struct.pack('>HHIHHBBBB',0xb006,method,len(body)+8,1,2,1,1,kind,0)+body


class BindingAuditTests(unittest.TestCase):
    def test_native_descriptor_and_binding(self):
        a=dict(resource_id=0x02000004,width=320,height=200,depth=0,packing=0,models={7:0x07000004})
        self.assertEqual(binding(frame(3,descriptor(a)))['resource'],0x02000004)
        self.assertEqual(binding(frame(11,detail(a)))['resource'],0x02000004)
        self.assertIsNone(binding(frame(3,descriptor(a),128)))

    def test_corrupt_identity_not_accepted(self):
        a=dict(resource_id=0x02000004,width=320,height=200,depth=0,packing=0)
        b=bytearray(descriptor(a));b[20]^=1
        with self.assertRaises(ValueError):binding(frame(3,b))
        p=frame(3,descriptor(a))
        for i in range(len(p)):
            with self.assertRaises(ValueError):binding(p[:i])

    def test_unknown_variant_not_inferred(self):
        a=dict(resource_id=0x02000004,width=320,height=200,depth=0,packing=0)
        b=bytearray(descriptor(a));b[16]=4
        self.assertIsNone(binding(frame(3,b)))
