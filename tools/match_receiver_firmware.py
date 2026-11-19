#!/usr/bin/env python3
"""Offline exact-ID/version inventory; never executes, extracts, or flashes files.
Names select candidates only. They do not authenticate contents or compatibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from capture_receiver_identity import decode_inventory

PATTERN=re.compile(r'^(?P<kind>[a-z]+)_(?P<id>[0-9a-f]{8})\.(?P<ext>bin|xml|caf)\.(?P<version>\d{3}_\d{3}_\d{3})$',re.I)
CATEGORIES={5:'cafd',6:'btld',7:'flsl',8:'swfl',13:'swfk'}


def targets(response):
    inv=decode_inventory(response)
    rows=[]
    for e in inv['entries']:
        kind=CATEGORIES.get(e['class_code'])
        if not kind:continue
        version='_'.join(f'{int(x):03d}' for x in e['version'].split('.'))
        rows.append(dict(kind=kind,id=e['id'],version=version,
                         role='coding metadata' if kind=='cafd' else 'software component',
                         expected_suffixes=['caf'] if kind=='cafd' else ['bin','xml']))
    return rows


def match(response,roots):
    wanted=targets(response);index={(t['kind'],t['id']):t for t in wanted}
    exact=[];other=[];unclassified=[];seen=set()
    for root in roots:
        if not root.is_dir():raise ValueError('Root must be an extracted directory: '+str(root))
        for path in root.rglob('*'):
            if not path.is_file() or path.is_symlink():continue
            m=PATTERN.fullmatch(path.name)
            if not m:
                if any(t['id'] in path.name.lower() for t in wanted):unclassified.append(str(path))
                continue
            d={k:v.lower() for k,v in m.groupdict().items()};target=index.get((d['kind'],d['id']))
            if not target:continue
            resolved=str(path.resolve())
            if resolved in seen:continue
            seen.add(resolved)
            row=dict(path=resolved,**d,bytes=path.stat().st_size)
            if d['version']!=target['version']:
                other.append(row);continue
            with path.open('rb') as f:row['sha256']=hashlib.file_digest(f,'sha256').hexdigest()
            row['content_identity_verified']=False
            exact.append(row)
    missing=[]
    for t in wanted:
        for ext in t['expected_suffixes']:
            if not any((r['kind'],r['id'],r['version'],r['ext'])==(t['kind'],t['id'],t['version'],ext) for r in exact):
                missing.append(f"{t['kind']}_{t['id']}.{ext}.{t['version']}")
    return dict(schema=1,response_sha256=hashlib.sha256(response).hexdigest(),targets=wanted,
                exact_filename_candidates=exact,other_versions=other,unclassified_target_names=unclassified,
                missing_expected_names=missing,roots=[str(p) for p in roots],
                firmware_contents_verified=False,renderer_match_proven=False,
                notes=['Extracted directories only; archives are not inspected or unpacked.',
                       'FLSL filename convention is a search candidate; retain unclassified matching-ID names.',
                       'Missing names do not prove a package lacks equivalent components under another layout.',
                       'A name match is not cryptographic provenance or a matching receiver implementation.'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--root',type=Path,action='append',default=[]);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    row=json.loads(a.capture.read_text());reply=bytes.fromhex(row['response_hex']);result=match(reply,a.root)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'targets':len(result['targets']),'exact_filename_candidates':len(result['exact_filename_candidates']),
                      'missing':len(result['missing_expected_names']),'renderer_match_proven':False}))
