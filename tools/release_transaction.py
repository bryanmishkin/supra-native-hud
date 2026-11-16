#!/usr/bin/env python3
"""Hash-guarded startup-file transaction. Local rehearsal by default.

The operator supplies an exact before/after file pair from the current target.
No guessed startup path, mount, restart, PID kill or network access is built in.
Produces an apply/rollback shell pair for QNX after validating scoped paths.
"""
import argparse,hashlib,json,re,shlex
from pathlib import Path

def digest(b):return hashlib.sha256(b).hexdigest()
def plan(target,before,after,out):
 if target not in ('/opt/sys/etc/starter.cfg','/opt/sys/etc/preloader-job-hu.cfg','/opt/nav/eceusa/bin/Appstarter.ini'):
  raise ValueError('Unreviewed startup target')
 old=before.read_bytes();new=after.read_bytes()
 if not old or not new or old==new or max(len(old),len(new))>512*1024:raise ValueError('Expected bounded distinct exact files')
 if b'\0' in old+new:raise ValueError('Text startup configuration required')
 out.mkdir(parents=True,exist_ok=False);(out/'before').write_bytes(old);(out/'after').write_bytes(new)
 token=digest(old)[:12]+'-'+digest(new)[:12]
 # cmp verifies exact bytes on QNX without relying on a particular hash utility.
 # Permissions are inherited with cp -p; no remount or automatic restart.
 quoted=shlex.quote(target);directory=shlex.quote(str(Path(target).parent));name=Path(target).name
 for action,expect,replacement in [('apply','before','after'),('rollback','after','before')]:
  script=f'''#!/bin/sh
set -eu
umask 077
cd "$(dirname "$0")"
TARGET={quoted}
[ ! -L "$TARGET" ] && [ -f "$TARGET" ] || exit 2
cmp "$TARGET" ./{expect} >/dev/null || {{ echo 'Target differs; refusing overwrite' >&2; exit 2; }}
LOCK={shlex.quote(str(Path(target).parent / ('.supra-hud-'+token+'.lock')))}
mkdir "$LOCK" || exit 2
TMP="$LOCK/{name}"
trap 'rm -f "$TMP"; rmdir "$LOCK"' EXIT HUP INT TERM
cp -p "$TARGET" "$TMP"
cat ./{replacement} > "$TMP"
cmp "$TMP" ./{replacement} >/dev/null || exit 2
cmp "$TARGET" ./{expect} >/dev/null || {{ echo 'Concurrent edit; refusing overwrite' >&2; exit 2; }}
mv "$TMP" "$TARGET"
sync
cmp "$TARGET" ./{replacement} >/dev/null || exit 2
printf '%s\\n' '{action.upper()}_VERIFIED'
'''
  p=out/(action+'.sh');p.write_text(script);p.chmod(0o700)
 (out/'transaction.json').write_text(json.dumps({'target':target,'before_sha256':digest(old),'after_sha256':digest(new),'installed':False,'requires_current_target_read':True,'restart_performed':False},indent=2))
 return token
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('target');p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('output',type=Path);a=p.parse_args();print(plan(a.target,a.before,a.after,a.output))
