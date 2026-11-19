"""Offline B00E lifecycle bodies; no sockets, IDs or vehicle changes."""
import struct

def _u32(v):
    if type(v) is not int or not 0 <= v <= 0xffffffff: raise ValueError('Expected u32')
    return struct.pack('>I',v)

def check_body(handle, resource_id, resource_type):
    if type(resource_type) is not int or not 0 <= resource_type <= 11: raise ValueError('Unsupported resource type')
    return _u32(handle)+_u32(resource_id)+bytes([resource_type])

def dispose_resource_body(handle, resource_id):
    return _u32(handle)+_u32(resource_id)

def check_reply(body, message_type=0x80, return_code=0):
    if message_type != 0x80 or return_code != 0 or body not in (b'\x00',b'\x01'): raise ValueError('Not a successful exact Boolean response')
    return body == b'\x01'

def dispose_reply(body, message_type=0x80, return_code=0):
    if message_type != 0x80 or return_code != 0 or body != b'': raise ValueError('Unexpected disposal response')
    return {'acknowledged':True,'resource_absent_verified':False,'visible_removal_verified':False}

if __name__=='__main__':
    assert check_body(100,0x01000000,1).hex()=='000000640100000001'
    assert dispose_resource_body(100,0x01000000).hex()=='0000006401000000'
    assert check_reply(b'\0') is False and check_reply(b'\1') is True
    for bad in [b'',b'\2',b'\1\0']:
        try: check_reply(bad)
        except ValueError: pass
        else: raise AssertionError(bad)
    print('Offline exact-body vectors passed; no ownership or live cleanup established.')
