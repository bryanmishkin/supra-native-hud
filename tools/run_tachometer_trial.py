#!/usr/bin/env python3
"""Three synthetic tach frames, each using a complete proven marker lifecycle.

No live RPM source, concurrent factory guidance or automatic takeover detection.
Preparation is offline. Live use is explicitly selected and bounded to 3x3sec.
"""
import argparse, hashlib, json, subprocess, sys, time, struct, zlib
from pathlib import Path

RPMS=(1000,3500,6500)

def png(raw):
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    rows=b''.join(b'\0'+b''.join(raw[i:i+3][::-1] for i in range(y*600,(y+1)*600,4)) for y in range(36))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',150,36,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')

def prepare(root):
    repo=Path(__file__).resolve().parents[1];root.mkdir(parents=True,exist_ok=False)
    exe=root/'tach-bitmap-demo'
    subprocess.run(['c++','-std=c++98','-Wall','-Wextra','-Werror','-I'+str(repo/'src'),str(repo/'src/hud_core.cpp'),str(repo/'src/tach_bitmap.cpp'),str(repo/'tools/tach_bitmap_demo.cpp'),'-o',str(exe)],check=True)
    from ric_rle32 import encode_bgra,decode_bgra
    frames=[]
    for rpm in RPMS:
        f=root/('%d.bgra'%rpm)
        subprocess.run([str(exe.resolve()),str(rpm),str(f)],check=True)
        raw=f.read_bytes();encoded=encode_bgra(raw)
        if decode_bgra(encoded,150*36)!=raw:raise ValueError('RLE roundtrip failed')
        f.with_suffix('.png').write_bytes(png(raw));f.with_suffix('.rle').write_bytes(encoded)
        frames.append(dict(rpm=rpm,file=f.name,sha256=hashlib.sha256(raw).hexdigest(),rle_bytes=len(encoded)))
    result=dict(synthetic=True,vehicle_thresholds_validated=False,scale_rpm=7000,shift_rpm=6500,frames=frames)
    (root/'frames.json').write_text(json.dumps(result,indent=2)+'\n');return result

def verified_frames(root):
    m=json.loads((root/'frames.json').read_text())
    if m.get('synthetic') is not True or [f['rpm'] for f in m['frames']]!=list(RPMS):raise ValueError('Expected three synthetic test frames')
    result=[]
    for f in m['frames']:
        if f['file']!='%d.bgra'%f['rpm']:raise ValueError('Unexpected frame path')
        p=root/f['file'];raw=p.read_bytes()
        if len(raw)!=21600 or any(x!=255 for x in raw[3::4]) or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise ValueError('Frame changed or invalid')
        result.append(p)
    return result

def run(args):
    frames=verified_frames(args.frames)
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(synthetic=True,automatic_navigation_detection=False,frames=[],status='running',visual_pass=False)
    def save():(args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        for i,frame in enumerate(frames):
            print('Synthetic RPM %d; engine does not need revving.'%RPMS[i],flush=True)
            cmd=[sys.executable,str(Path(__file__).with_name('run_shared_roadicon_trial.py')),'--execute','--guidance-stopped','--bitmap-bgra',str(frame),'--window-seconds','3',
                 '--create-response',str(args.create_response),'--support-stream',str(args.support_stream),'--ssh-socket',str(args.ssh_socket),'--head',args.head,'--output',str(args.output/('frame-%d'%i))]
            # Child performs bounded cleanup on SIGINT; never start the next child
            # until it has exited and all cleanup checks have been inspected.
            child=subprocess.Popen(cmd)
            try:rc=child.wait()
            except KeyboardInterrupt:
                import signal
                child.send_signal(signal.SIGINT)
                child.wait(timeout=90)
                raise
            result=json.loads((args.output/('frame-%d'%i)/'result.json').read_text())
            report['frames'].append(dict(rpm=RPMS[i],returncode=rc,result=result));save()
            resources=result.get('cleanup',{}).get('resources',[])
            steps=result.get('cleanup_steps',[])
            if (rc or result.get('status')!='awaiting_visual_verification' or result.get('forward_cancelled') is not True or not resources or not steps or
                not all(x.get('acknowledged') is True for x in steps) or
                not all(x.get('dispose_acknowledged') is True and x.get('post_dispose_check') is False for x in resources)):
                raise RuntimeError('Cleanup not verified; sequence stopped. Do not restart automatically.')
            time.sleep(1)
        report['status']='awaiting_visual_and_factory_navigation_checks'
    except (Exception,KeyboardInterrupt) as e:
        report['status']='stopped';report['error']=str(e) or type(e).__name__
    finally:save()
    print('Test ended. Confirm all test graphics gone BEFORE starting factory guidance. Check navigation and radio in both displays.',flush=True)
    return 0 if report['status']=='awaiting_visual_and_factory_navigation_checks' else 2

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare',type=Path);p.add_argument('--execute',action='store_true');p.add_argument('--guidance-stopped',action='store_true')
    for name in ('frames','output','create-response','support-stream','ssh-socket'):p.add_argument('--'+name,type=Path)
    p.add_argument('--head')
    a=p.parse_args()
    if a.prepare:
        if a.execute:p.error('Preparation and execution are separate')
        print(json.dumps(prepare(a.prepare),indent=2));return 0
    if not a.execute:
        print('Offline plan: three synthetic tach frames; 3 seconds each, complete withdrawal/disposal/absence check between frames. Factory guidance must stay stopped; after cleanup, verify factory navigation and radio. No automatic navigation arbitration.');return 0
    if not a.guidance_stopped or not all((a.frames,a.output,a.create_response,a.support_stream,a.ssh_socket,a.head)):
        p.error('Execution requires all paths, head address and --guidance-stopped')
    import signal
    def stop(sig,frame):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,stop)
    return run(a)
if __name__=='__main__':sys.exit(main())
