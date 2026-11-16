#!/bin/sh
# Switch only project-owned release pointers. Factory startup rollback is separate.
set -eu
umask 077
command -v sync >/dev/null 2>&1 || { echo 'Required sync utility unavailable; no changes' >&2; exit 2; }
[ "$#" -ge 3 ] || exit 64
ROOT=$1
STATE=$2
ACTION=$3
shift 3
case "$ROOT:$STATE" in /*:/*) ;; *) exit 64;; esac
[ ! -L "$ROOT/current" ] && [ ! -L "$ROOT/previous" ] || exit 2
mkdir "$ROOT/transition.lock" || exit 2
TMP="$ROOT/transition.lock/current"
trap 'rm -f "$TMP"; rmdir "$ROOT/transition.lock"' EXIT HUP INT TERM
case "$ACTION" in
activate) [ "$#" = 1 ] || exit 64; target=$1;;
rollback) [ "$#" = 0 ] || exit 64; target=$(cat "$ROOT/previous");;
*) exit 64;;
esac
case "$target" in ''|*[!0-9a-f]*) exit 64;; esac
[ ! -L "$ROOT/releases/$target" ] && [ -d "$ROOT/releases/$target" ] || exit 2
[ "$(cat "$ROOT/releases/$target/release.ok")" = "$target" ] || exit 2
# Always stop before changing the selected executable. Uncertain stop aborts switch.
"${0%/*}/hud-service.sh" "$ROOT" "$STATE" disable
old=''
if [ -f "$ROOT/current" ]; then old=$(cat "$ROOT/current"); fi
case "$old" in *[!0-9a-f]*) exit 2;; esac
echo "$target" > "$TMP"
if [ -n "$old" ]; then echo "$old" > "$ROOT/previous"; fi
mv "$TMP" "$ROOT/current"
sync
[ "$(cat "$ROOT/current")" = "$target" ] || exit 2
echo 'RELEASE_SELECTED_DISABLED'
