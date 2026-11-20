"""Bounded two-image trial engine using the unchanged accepted V1 graph.
No sockets or vehicle connection here; caller supplies verified transport and
admission. Never creates/disposes the shared instance or modifies V1 files.
"""
import hashlib,struct,time
from ric_road_list import decode,encode,two_image_candidates
from prepare_road_list_expansion import marker
from ric_rle32 import encode_bgra,swap_red_blue
from ric_resource import encode_bitmap_body
PROFILE_SHA='f621e800338a3225f9fecf20f98b6938034aafb4f6bebb208e1ea156b89f4791'


def profile_commands(raw,case):
    if hashlib.sha256(raw).hexdigest()!=PROFILE_SHA:raise ValueError('Expected accepted symbol-free V1 profile')
    rows=[];off=8
    for _ in range(17):
        m,n=struct.unpack_from('>HI',raw,off);off+=6;rows.append((m,raw[off:off+n]));off+=n
    if off!=len(raw):raise ValueError('Invalid profile length')
    road=rows[4][1];base=decode(road);base['entries'][0]['resources']=[0x01000008];road=encode(base)
    candidates=two_image_candidates(road,0x01000008,0x01000009)
    if case=='control':chosen=road
    elif case in ('two_icons_one_entry','one_icon_two_entries'):chosen=candidates[case]
    elif case=='wide_tail_64':chosen=candidates['one_icon_two_entries']
    elif case=='right_boundary_ruler':
        value=decode(candidates['one_icon_two_entries']);value['alignment']=1;chosen=encode(value)
    else:raise ValueError('Unknown structural case')
    if rows[4][0]!=14 or rows[15]!=(14,candidates['withdraw']):raise ValueError('Unrecognized graph/cleanup')
    rows[4]=(14,chosen)
    return rows[:10],rows[10:]


def run(session,profile,case,record,observe,begin_cleanup=lambda:None):
    """observe provides a bounded30second window; never infers visual success."""
    setup,cleanup=profile_commands(profile,case)
    images=[]
    for number,rid in ((1,0x01000008),(2,0x01000009)):
        if case=='control' and number==2:continue
        width,height=150,36
        if case=='wide_tail_64':
            from road_extent_probe import image
            width,height,pixels=image(number-1)
        elif case=='right_boundary_ruler':
            from road_boundary_ruler import tile
            pixels=tile(number-1)
        else:pixels=marker(number)
        images.append((rid,width,height,pixels))
    return run_plan(session,setup,cleanup,images,case,record,observe,begin_cleanup)


def run_plan(session,setup,cleanup,images,case,record,observe,begin_cleanup=lambda:None):
    """Execute a compiled bounded graph with the same fail-closed removal policy.

    Callers must independently validate model allocation and graph contracts.
    This engine is not admission for arbitrary factory model writes.
    """
    ids=[image[0] for image in images]
    if not ids or len(ids)!=len(set(ids)) or set(ids)-{0x01000008,0x01000009}:
        raise ValueError('Only distinct reserved image slots accepted')
    for rid,width,height,pixels in images:
        if not (type(width) is int and type(height) is int and 0<width<=150 and 0<height<=36 and len(pixels)==width*height*4):
            raise ValueError('Image exceeds measured bitmap contract')
    result=dict(case=case,status='preflight',graph_attempted=False,uploaded=[],cleanup=[],visual_success=False)
    cleaning=False
    def save():
        result['journal']=session.journal
        try:record(result)
        except Exception as e:
            result.setdefault('recording_errors',[]).append(str(e))
            if not cleaning:raise
    tracked=[]
    try:
        # Both slots must be free, even for the one-image control.
        for rid in (0x01000008,0x01000009):
            if session._check(rid,1):raise ValueError('Tach image slot occupied')
        for rid,width,height,pixels in images:
            if session._check(rid,1):raise ValueError('Slot became occupied')
            tracked.append(rid);session.resources[rid]=1;save() # lost ACK remains tracked
            result.setdefault('image_geometry',[]).append(dict(resource_id=rid,width=width,height=height,pixel_sha256=hashlib.sha256(pixels).hexdigest()))
            save()
            body=encode_bitmap_body(200,rid,1,[width,height],encode_bgra(swap_red_blue(pixels)))
            session._empty(3,body)
            if not session._check(rid,1):raise ValueError('Image upload absent')
            result['uploaded'].append(rid);save()
        result['graph_attempted']=True;save()
        for m,b in setup:session._empty(m,b);save()
        result['status']='visible_window';save()
        observe(30)
        result['status']='window_finished'
    except (Exception,KeyboardInterrupt) as e:
        result['status']='failed_or_interrupted';result['error']=str(e) or type(e).__name__
    finally:
        cleaning=True
        begin_cleanup()
        detached=True
        if result['graph_attempted']:
            for m,b in cleanup:
                item=dict(method=m,ack=False);result['cleanup'].append(item)
                try:session._empty(m,b);item['ack']=True
                except Exception as e:item['error']=str(e);detached=False
                save()
        result['detachment_acknowledged']=detached
        result['resource_removal']=[]
        if detached:
            for rid in tracked:
                item=dict(resource_id=rid,dispose_ack=False,absent=False);result['resource_removal'].append(item)
                try:session._empty(8,struct.pack('>II',200,rid));item['dispose_ack']=True
                except Exception as e:item['dispose_error']=str(e)
                try:item['absent']=not session._check(rid,1)
                except Exception as e:item['check_error']=str(e)
                save()
        else:result['retained_due_to_uncertain_detachment']=tracked
        result['protocol_cleanup_passed']=bool(tracked) and detached and all(x['dispose_ack'] and x['absent']for x in result['resource_removal'])
        result['v1_restored']=False
        save()
    return result
