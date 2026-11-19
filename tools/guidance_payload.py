"""Offline DNAVIManeuverView payload codecs; no service connection or drawing.
Numeric fields and string encoding require captured-native differential verification.
Dimensions are protocol inputs, never assertions of supported windshield geometry.
"""
import struct

def u32(value):
    if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<=0xffffffff:
        raise ValueError('Expected unsigned 32-bit integer')
    return struct.pack('<I',value)

def text(value):
    if not isinstance(value,str) or '\x00' in value:
        raise ValueError('Expected text without embedded NUL')
    raw=value.encode('utf-8')
    if len(raw)>4096:raise ValueError('Local string budget exceeded')
    # Native CHBString writer uses byte length, excludes terminator, no padding.
    return u32(len(raw))+raw

def register_guidance(maneuver_id,guidance_type,style_client=3):
    u32(guidance_type);u32(style_client)
    if not 0<=guidance_type<=0xffffff or not 0<=style_client<=0x7f:
        raise ValueError('Invalid guidance type/style client')
    return u32(maneuver_id)+u32(guidance_type|(style_client<<24))

def attach_guidance(guidance_session,displayable_session):
    return u32(guidance_session)+u32(displayable_session)

def register_displayable(user_id,view_type,width,height,options=()):
    options=list(options)
    if len(options)>32:raise ValueError('Local option budget exceeded')
    return b''.join(u32(x)for x in (user_id,view_type,width,height,len(options)))+b''.join(text(k)+text(v)for k,v in options)

def unregister_guidance():
    # The owned MOCCA request sequence belongs in the envelope, not this payload.
    return b''

def set_ric_maneuver_content(guidance_session,ric_maneuver_id):
    u32(ric_maneuver_id)
    # Factory formatter uses signed decimal %d. Preserve the u32 bit pattern.
    signed=ric_maneuver_id if ric_maneuver_id<0x80000000 else ric_maneuver_id-(1<<32)
    return b''.join(u32(x)for x in (guidance_session,1,5,7))+text('RICManeuverID=%d'%signed)

def decode_displayable_data(payload):
    """Decode response 0x80000004; metadata only, never opens shared memory.

    Length/sequence must be checked against the owned displayable and its actual
    publication before using its bytes. Neither an event nor its name proves
    receiver routing or a visible frame.
    """
    if not isinstance(payload,bytes) or len(payload)<24:
        raise ValueError('Truncated displayable data')
    user_id,length=struct.unpack_from('<II',payload)
    if length>4096 or len(payload)!=24+length:
        raise ValueError('Invalid displayable name length or trailing bytes')
    raw=payload[8:8+length]
    if b'\0' in raw:raise ValueError('Embedded NUL in shared-memory name')
    name=raw.decode('utf-8',errors='strict')
    maneuver,guidance_type,byte_count,sequence=struct.unpack_from('<IIII',payload,8+length)
    return dict(user_id=user_id,shared_memory_name=name,
                maneuver_id=maneuver,guidance_type=guidance_type,byte_count=byte_count,sequence=sequence)

def unregister_displayable():
    return b''

def displayable_handshake(sequence,user_id,view_type,width,height,options=()):
    """Owned registry subscription followed by creation, on ONE client route.

    Sequence is allocated by the caller's live framework. This is a request
    description, not a socket operation or evidence of receiver acceptance.
    """
    u32(sequence)
    if not sequence:raise ValueError('Owned registration sequence must be nonzero')
    return [dict(request_type=0x105,event_id=0x80000004,sequence=sequence,payload=b''),
            dict(request_type=0x100,event_id=4,sequence=sequence,
                 payload=register_displayable(user_id,view_type,width,height,options))]

def displayable_release_requests(sequence):
    """Remove only this registry listener, then dispose this displayable.

    A transport must finish its owned pixel-removal protocol first. Sending
    these requests is not an image-removal acknowledgment.
    """
    u32(sequence)
    if not sequence:raise ValueError('Owned registration sequence must be nonzero')
    return [dict(request_type=0x106,event_id=0x80000004,sequence=sequence,payload=b''),
            dict(request_type=0x100,event_id=6,sequence=sequence,payload=b'')]
