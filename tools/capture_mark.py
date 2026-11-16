#!/usr/bin/env python3
"""Append a host-clock action marker to an active capture folder. No network access."""
import argparse,json,time
from pathlib import Path
def mark(folder,label):
    if label not in ('baseline','radio-open','radio-close','guidance-start','guidance-stop','ignition-off','ignition-on','factory-normal'):raise ValueError('Unknown action marker')
    state=json.loads((folder/'status.json').read_text());now=time.time()
    if (folder/'result.json').exists() or not 0<=now-state['ready_seen_epoch']<=140:raise ValueError('Capture is not active')
    with (folder/'markers.jsonl').open('a') as f:f.write(json.dumps(dict(label=label,host_epoch=now))+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('label');a=p.parse_args()
    try:mark(a.folder,a.label)
    except (OSError,ValueError,KeyError) as e:p.exit(2,str(e)+'\n')
