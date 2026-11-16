#!/usr/bin/env python3
"""Request cooperative withdrawal from a running parked RPM test.

This is local IPC only. It does not start navigation or establish cleanup success.
"""
import argparse,json
from pathlib import Path
TOKEN='factory-navigation\n'
class NavigationYield(Exception):pass

def check_yield(root):
    p=Path(root)/'navigation-yield.request'
    if not p.exists():return
    if p.stat().st_size>64 or p.read_text()!=TOKEN:raise ValueError('Malformed yield request; stopping test')
    raise NavigationYield('Factory navigation requested')

def request(root):
    root=Path(root)
    # Request only an existing active trial; never create a new trial directory.
    result=json.loads((root/'result.json').read_text())
    if result.get('status')!='observing_marker' or result.get('live_rpm') is not True:raise ValueError('Trial is not in its observation window')
    with (root/'navigation-yield.request').open('x') as f:f.write(TOKEN)

def handoff_ready(report):
    c=report.get('cleanup',{});resources=c.get('resources',[]);steps=report.get('cleanup_steps',[])
    return (report.get('status')=='awaiting_visual_verification' and report.get('stop_reason')=='factory_navigation_request'
        and report.get('forward_cancelled') is True and c.get('shared_instance_preserved') is True
        and bool(resources) and bool(steps) and all(s.get('acknowledged') is True for s in steps)
        and all(r.get('dispose_acknowledged') is True and r.get('post_dispose_check') is False for r in resources))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path);a=p.parse_args();request(a.trial)
    print('Yield requested. Wait for navigation-handoff.json and visual removal confirmation before starting guidance.')
