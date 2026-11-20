"""Offline model40 road-list codec. No transport or visible-layout claim.

Entries carry an array of resource IDs and two trailing bytes. The latter are
preserved as opaque values until their semantic enum names are established.
"""
import struct
from ric_lifecycle import Reader


def u32(n):
    if type(n) is not int or not 0 <= n <= 0xffffffff:
        raise ValueError('Expected u32')
    return struct.pack('>I',n)


def decode(body):
    r=Reader(body)
    handle,model,kind=r.u32(),r.u32(),r.take(1)[0]
    size,tag=r.u32(),r.u32()
    p=Reader(r.take(size));r.finish()
    if kind!=40 or tag!=2:raise ValueError('Expected model40/tag2')
    if p.u32()!=model or p.take(1)[0]!=kind:raise ValueError('Inner identity mismatch')
    road_type,alignment=p.take(2)
    if road_type>1 or alignment>1:raise ValueError('Untraced road type/alignment')
    entries=Reader(p.take(p.u32()));p.finish();rows=[]
    while entries.pos<len(entries.data):
        n=entries.u32()
        if n%4 or n>40:raise ValueError('Invalid resource array extent')
        ids=[entries.u32() for _ in range(n//4)]
        tail=list(entries.take(2))
        rows.append(dict(resources=ids,trailing_bytes=tail))
        if len(rows)>10:raise ValueError('Exceeds captured entry limit')
    return dict(handle=handle,model_id=model,road_type=road_type,alignment=alignment,entries=rows)


def encode(value):
    rows=value['entries']
    if len(rows)>10:raise ValueError('Exceeds captured entry limit')
    entries=bytearray()
    for row in rows:
        ids=row['resources'];tail=row['trailing_bytes']
        if len(ids)>10 or len(tail)!=2 or any(type(x)is not int or not 0<=x<=255 for x in tail):
            raise ValueError('Invalid entry')
        data=b''.join(u32(x) for x in ids)
        entries.extend(u32(len(data))+data+bytes(tail))
    if value['road_type'] not in (0,1) or value['alignment'] not in (0,1):raise ValueError('Untraced road type/alignment')
    model=u32(value['model_id'])
    payload=model+b'\x28'+bytes([value['road_type'],value['alignment']])+u32(len(entries))+entries
    return u32(value['handle'])+model+b'\x28'+u32(len(payload))+u32(2)+payload


def two_image_candidates(template,first,second):
    """Derive two distinct structural candidates; not a live admission function."""
    base=decode(template)
    if len(base['entries'])!=1 or len(base['entries'][0]['resources'])!=1:
        raise ValueError('Expected proven one-image control template')
    if first==second or any(x not in (0x01000008,0x01000009) for x in (first,second)):
        raise ValueError('Use two distinct tach image slots, only after V1 pause and absence checks')
    import copy
    one_row=copy.deepcopy(base);one_row['entries'][0]['resources']=[first,second]
    two_rows=copy.deepcopy(base)
    two_rows['entries'][0]['resources']=[first]
    row=copy.deepcopy(two_rows['entries'][0]);row['resources']=[second]
    two_rows['entries'].append(row)
    empty=copy.deepcopy(base);empty['entries']=[]
    return dict(two_icons_one_entry=encode(one_row),one_icon_two_entries=encode(two_rows),withdraw=encode(empty))
