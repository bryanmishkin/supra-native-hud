#!/usr/bin/env python3
"""Compare read-only factory GVCommand snapshots by manually labeled HUD stage.

Shows correlation, not proof of on-screen geometry, display destination or ownership.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def compare(manifests):
    result={'schema':1,'stages':[], 'displayables':{},'destination_proven':False,
            'limitation':'Buffers may be stale/reusable and stages are observer labels; changed bytes do not establish projected pixels.'}
    by_id=defaultdict(lambda:defaultdict(set))
    for stage,m in manifests:
        if not m.get('complete'):
            raise ValueError('Incomplete stage cannot be interpreted as absence')
        result['stages'].append(dict(stage=stage,buffer_count=len(m.get('buffers',[])),
                                     objects=m.get('objects_discovered')))
        for row in m.get('buffers',[]):
            if not row.get('saved'):
                continue
            ident=row['displayable_id'];name=row['name'];by_id[ident][stage].add((name,row['sha256']))
    for ident, states in sorted(by_id.items()):
        stages={k:sorted(v) for k,v in states.items()}
        keys={k:{n for n,_ in v} for k,v in stages.items()}
        union=set().union(*keys.values())
        changes={}
        for name in union:
            found={k:sorted(h for n,h in v if n==name) for k,v in stages.items()}
            differing={tuple(v) for v in found.values() if v}
            if len(differing)>1 or len({bool(v) for v in found.values()})>1:
                changes[name]=found
        result['displayables'][str(ident)]=dict(stage_names=list(stages),
            unique_buffer_hashes=len(set(h for rows in stages.values() for _,h in rows)),
            changed_by_stage=changes,
            projection_assignment='unverified')
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage_dirs',nargs='+',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args(argv)
    if len(a.stage_dirs)<2:p.error('Use at least two stage directories')
    try:
        manifests=[]
        for folder in a.stage_dirs:
            doc=json.loads((folder/'manifest.json').read_text())
            manifests.append((doc['stage'],doc))
        result=compare(manifests)
        raw=json.dumps(result,indent=2)+'\n'
        if a.output:
            if a.output.exists():raise ValueError('Refusing to overwrite report')
            a.output.write_text(raw)
        print(raw)
        return 0
    except (OSError,ValueError,KeyError) as exc:p.exit(2,str(exc)+'\n')
if __name__=='__main__':raise SystemExit(main())

