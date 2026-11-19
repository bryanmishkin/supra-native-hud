"""Offline Entertainment table codec from HMI writers; no network access.

The six u16 metadata values remain opaque here. A row selection is explicit,
not guessed from those fields. Content columns >=1 have a bitmap-producing
factory path; receiver rendering is not established by encoding.
"""
import struct
from ric_lifecycle import Reader

MAX_ROWS=256
MAX_COLUMNS=32

def _int(value,bits):
    if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Invalid unsigned integer')
    return value

def _u32(v):return struct.pack('>I',_int(v,32))

def encode(handle,model_id,model_type,metadata,header_reference,rows,trailing_references):
    if model_type!=0x16:raise ValueError('Expected Entertainment type')
    if not isinstance(metadata,(list,tuple)) or len(metadata)!=6:raise ValueError('Expected six metadata words')
    if not isinstance(rows,(list,tuple)) or len(rows)>MAX_ROWS:raise ValueError('Invalid row count')
    table=[]
    for row in rows:
        if not isinstance(row,(list,tuple)) or len(row)>MAX_COLUMNS:raise ValueError('Invalid column count')
        cells=[]
        for cell in row:
            if not isinstance(cell,(list,tuple)) or len(cell)!=2:raise ValueError('Expected resource/state cell')
            cells.append(_u32(cell[0])+bytes([_int(cell[1],8)]))
        data=b''.join(cells);table.append(_u32(len(data))+data)
    if not isinstance(trailing_references,(list,tuple)) or len(trailing_references)!=4:raise ValueError('Expected four trailing references')
    table=b''.join(table)
    payload=(_u32(model_id)+bytes([model_type])+struct.pack('>6H',*[_int(v,16) for v in metadata])+
             _u32(header_reference)+_u32(len(table))+table+b''.join(_u32(v) for v in trailing_references))
    if len(payload)>65536-17:raise ValueError('Model body too large')
    return _u32(handle)+_u32(model_id)+bytes([model_type])+_u32(len(payload))+_u32(3)+payload

def decode(body):
    r=Reader(body);handle=r.u32();mid=r.u32();typ=r.take(1)[0];n=r.u32();tag=r.u32();b=Reader(r.take(n));r.finish()
    if (typ,tag)!=(0x16,3):raise ValueError('Expected Entertainment variant')
    if b.u32()!=mid or b.take(1)[0]!=typ:raise ValueError('Mismatched model identity')
    metadata=list(struct.unpack('>6H',b.take(12)));header=b.u32();table=Reader(b.take(b.u32()));rows=[]
    while table.pos<len(table.data):
        if len(rows)>=MAX_ROWS:raise ValueError('Too many rows')
        size=table.u32()
        if size%5 or size>MAX_COLUMNS*5:raise ValueError('Invalid cell-array length')
        cells=Reader(table.take(size));row=[]
        while cells.pos<len(cells.data):row.append([cells.u32(),cells.take(1)[0]])
        rows.append(row)
    trailing=[b.u32() for _ in range(4)];b.finish()
    return dict(handle=handle,model_id=mid,model_type=typ,metadata=metadata,header_reference=header,rows=rows,trailing_references=trailing)

def replace_content_cell(body,resource_id,row_index,column_index):
    """Change only one content resource, preserving all state and metadata.

    row_index is zero-based within the transmitted array, not a guessed
    selection or absolute station number. Column zero is the separate icon.
    """
    m=decode(body)
    if (m['handle'],m['model_id'],m['model_type'])!=(100,0x66,0x16):raise ValueError('Expected factory Entertainment snapshot')
    if encode(**m)!=body:raise ValueError('Snapshot round-trip mismatch')
    _int(resource_id,32)
    if resource_id==0xffffffff:raise ValueError('Expected image resource')
    if type(row_index) is not int or not 0<=row_index<len(m['rows']):raise ValueError('Row outside captured table')
    if type(column_index) is not int or not 1<=column_index<len(m['rows'][row_index]):raise ValueError('Expected existing content column, not icon')
    m['rows'][row_index][column_index][0]=resource_id
    return encode(**m)
