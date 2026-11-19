"""Offline high-guidance bitmap candidate. No transport or V1 modification."""
import struct
from ric_graph import encode_description_body
from ric_guiding import encode_high_roundabout_body
from pip_trial import measured_support

ABSENT=0xffffffff

def build_candidate(support_profile, allocation, *, threshold):
    """Build paired 92/1000m experiments using the same 150x36 bitmap.

    High-guidance physical extent and receiver acceptance remain unverified.
    Allocation must come from the existing guarded B006 admission workflow.
    """
    if threshold not in (92.0,1000.0):
        raise ValueError('Only historical control92 and candidate1000 allowed')
    if allocation.get('handle')!=200 or allocation.get('dimensions') not in ([150,36],(150,36)):
        raise ValueError('Expected measured shared B006 bitmap geometry')
    models=allocation.get('models',{})
    expected={10:0x0a000004,15:0x0f000004,17:0x11000000,29:0x1d00001d,34:0x22000004}
    if any(models.get(k)!=v for k,v in expected.items()):
        raise ValueError('Measured model allocation mismatch')
    rid=allocation.get('resource_id')
    if rid not in (0x01000008,0x01000009):
        raise ValueError('Only baseline reserved bitmap slots accepted')
    measured=measured_support(support_profile,dict(allocation))
    current=bytearray.fromhex(measured['support_start'][0][1])
    struct.pack_into('>d',current,38,threshold)
    high=encode_high_roundabout_body(200,models[10],10,0,2,rid)
    description=encode_description_body(200,models[15],15,is_passive=False,
        previous_joined=False,previous_maneuver_id=ABSENT,next_joined=False,
        next_maneuver_id=ABSENT,maneuver_direction=14,coming_road_id=ABSENT,
        current_state_id=models[34],detailed_maneuver_id=models[10],distance_id=models[29],
        navigation_event_ids=[],lane_guiding_ids=[],point_of_interest_ids=[])
    return dict(threshold=threshold,dimensions=[150,36],resource_id=rid,
        setup=[(10,bytes(current)),(10,bytes.fromhex(measured['support_start'][1][1])),
               (11,high),(10,description)],
        position_start=bytes.fromhex(measured['position_start']),
        position_stop=bytes.fromhex(measured['position_stop']),
        clear_high=encode_high_roundabout_body(200,models[10],10,0,2,ABSENT),
        larger_extent_proven=False,live_admission_proven=False)
