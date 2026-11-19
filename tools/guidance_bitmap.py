"""Offline decoding of an owned, uncompressed type-1 guidance bitmap snapshot.

Never opens or acknowledges shared memory. Actual live copying/acknowledgment
requires the native mutex and a verified owned registration; the first eight
header bytes are not portable lock data and must never be modified offline.
"""
import struct

def decode_owned_rgba(metadata,snapshot,*,user_id,maneuver_id,guidance_type,
                      sequence,width,height):
    for name,value in [('width',width),('height',height)]:
        if not isinstance(value,int) or isinstance(value,bool) or not 1<=value<=2048:
            raise ValueError(name+' outside local analysis budget')
    for name,value in [('user_id',user_id),('maneuver_id',maneuver_id),
                       ('guidance_type',guidance_type),('sequence',sequence)]:
        if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<=0xffffffff:
            raise ValueError('Invalid expected '+name)
        if metadata.get(name)!=value:raise ValueError('Metadata ownership mismatch: '+name)
    if sequence in (0xfffffffe,0xffffffff):raise ValueError('Released/invalid sequence')
    if not isinstance(snapshot,bytes) or len(snapshot)!=12+width*height*4:
        raise ValueError('Raw RGBA snapshot has unexpected size')
    if metadata.get('byte_count')!=len(snapshot):raise ValueError('Publication size mismatch')
    if struct.unpack_from('<I',snapshot,8)[0]!=sequence:
        raise ValueError('Stale or released shared-memory publication')
    return dict(width=width,height=height,format='RGBA',row_order='top-down',
                pixels=snapshot[12:],limitation='Offline raw type-1 interpretation only; no claim of live ownership, mutex synchronization, acknowledgment or windshield routing.')
