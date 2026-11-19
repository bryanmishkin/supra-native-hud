"""Native PiP metadata record builder; no sockets, Screen or vehicle operations.

Inputs must come from the owned producer. A valid record is not proof of a
receiver association. BGRA conversion is deliberately not inferred here.
"""
import struct
from pip_metadata_strip import encode_record


def build_record(guidance_type, picture, maneuver_id, style_flag, option_zero=0):
    for name,value,maximum in [('guidance_type',guidance_type,0xffffff),
                               ('picture',picture,0xffff),
                               ('maneuver_id',maneuver_id,0xffffffff),
                               ('option_zero',option_zero,255)]:
        if type(value) is not int or not 0<=value<=maximum:
            raise ValueError('Invalid '+name)
    if type(style_flag) is not bool:
        raise ValueError('style_flag must be the resolved native boolean')
    record=bytearray(84)
    struct.pack_into('<H',record,2,picture)
    record[4]=1
    record[5]=option_zero
    record[6]=0 if style_flag else 1
    # Both captured junction and intersection renderers use this exact test.
    # This producer byte differs for HUD style group8. Receiver semantics are
    # not inferred solely from its correlation with the view-type group.
    record[7]=int(((guidance_type//1000)&255)!=8)
    struct.pack_into('<I',record,16,maneuver_id)
    return bytes(record)


def build_cpu_upload(*args,**kwargs):
    return encode_record(build_record(*args,**kwargs))
