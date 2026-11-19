"""Offline B00E carousel/voice body codec, derived from captured HMI writers.

Field 1 is the factory icon reference. Custom bitmap acceptance is unproven.
This module neither chooses session/model IDs nor transmits messages.
"""
import struct
from ric_lifecycle import Reader

def u32(value):
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('Expected u32')
    return struct.pack('>I',value)

def encode(handle,model_id,model_type,index,elements,trailing):
    if model_type not in (0x1c,0x2f):raise ValueError('Expected Carousel or Voice type')
    if type(index) is not int or not 0<=index<=255:raise ValueError('Expected byte index')
    if not isinstance(trailing,bytes) or len(trailing)!=3:raise ValueError('Expected three trailing bytes')
    if not isinstance(elements,(list,tuple)) or len(elements)>4:raise ValueError('Bounded to four advertised elements')
    rows=[]
    for row in elements:
        if not isinstance(row,(list,tuple)) or len(row)!=4:raise ValueError('Expected four reference fields')
        rows.append(b''.join(u32(v) for v in row))
    items=b''.join(rows)
    payload=u32(model_id)+bytes([model_type,index])+u32(len(items))+items+trailing
    return u32(handle)+u32(model_id)+bytes([model_type])+u32(len(payload))+u32(8 if model_type==0x1c else 10)+payload

def decode(body):
    r=Reader(body);handle=r.u32();mid=r.u32();typ=r.take(1)[0];n=r.u32();tag=r.u32();b=Reader(r.take(n));r.finish()
    if (typ,tag) not in ((0x1c,8),(0x2f,10)):raise ValueError('Unexpected carousel/voice variant')
    if b.u32()!=mid or b.take(1)[0]!=typ:raise ValueError('Mismatched model identity')
    index=b.take(1)[0];n=b.u32()
    if n%16 or n>64:raise ValueError('Invalid bounded element array')
    elements=[list(struct.unpack('>IIII',b.take(16))) for _ in range(n//16)]
    trailing=b.take(3);b.finish()
    return dict(handle=handle,model_id=mid,model_type=typ,index=index,elements=elements,trailing=trailing)
