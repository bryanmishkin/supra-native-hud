#!/bin/sh
# App-owned lifecycle only. This script never edits factory startup or kills a PID.
set -eu
umask 077
[ "$#" -ge 3 ] || { echo 'usage: hud-service.sh ROOT RAM_STATE startup|status|start-parked|stop|disable' >&2; exit 64; }
ROOT=$1
STATE=$2
ACTION=$3
shift 3
case "$ROOT:$STATE" in /*:/*) ;; *) exit 64;; esac
mkdir -p "$ROOT" "$STATE"
release=''
if [ -f "$ROOT/current" ]; then release=$(cat "$ROOT/current"); fi
case "$release" in *[!0-9a-f]*|'') release='';; esac
DIR="$ROOT/releases/$release"
stop_worker() {
    if [ ! -d "$STATE/lock" ]; then echo 'STOPPED'; return 0; fi
    [ -n "$release" ] || return 2
    "$DIR/supra-hud-control-qnx" "$STATE/active.jsonl.handoff" || return 2
    # CLEAN is protocol evidence. Wait for the actual owning wrapper to finish.
    count=0
    while [ -d "$STATE/lock" ] && [ "$count" -lt 8 ]; do sleep 1; count=$((count+1)); done
    [ ! -d "$STATE/lock" ] || return 2
}
case "$ACTION" in
startup)
    # A boot is never evidence that factory guidance is stopped.
    # Start management in standby; only explicit fresh parked confirmation draws.
    echo 'standby: fresh guidance/ownership confirmation required' > "$STATE/startup-state"
    if [ ! -f "$ROOT/enabled" ]; then : > "$ROOT/disabled"; fi
    ;;
status)
    if [ -f "$ROOT/disabled" ]; then echo DISABLED
    elif [ -d "$STATE/lock" ]; then echo RUNNING_OR_QUARANTINED
    else echo STANDBY; fi
    ;;
start-parked)
    [ "${1:-}" = '--guidance-stopped-and-parked' ] && [ "$#" = 1 ] || exit 64
    [ -n "$release" ] && [ -f "$ROOT/enabled" ] && [ ! -f "$ROOT/disabled" ] || { echo 'Not enabled' >&2; exit 2; }
    [ "$(cat "$DIR/release.ok")" = "$release" ] || { echo 'Release validation mismatch' >&2; exit 2; }
    mkdir "$STATE/lock" || { echo 'Existing owner or unresolved prior run' >&2; exit 2; }
    # Stale journal/socket must be investigated rather than silently removed.
    if [ -e "$STATE/active.jsonl" ] || [ -e "$STATE/active.jsonl.handoff" ]; then
        : > "$ROOT/disabled"; echo 'Unarchived prior run; disabled' >&2; exit 2
    fi
    export SUPRA_HUD_DISABLE_FILE="$ROOT/disabled"
    export SUPRA_HUD_HANDOFF="$STATE/active.jsonl.handoff"
    "$DIR/supra-standalone-parked-qnx" --parked-guidance-stopped "$DIR/supra-profile.bin" \
        169.254.199.119 169.254.106.96 160.48.199.96 vlan73 30 "$STATE/active.jsonl" \
        > "$STATE/result.pending" 2> "$STATE/worker.stderr" &
    child=$!
    trap '"$DIR/supra-hud-control-qnx" "$STATE/active.jsonl.handoff" >/dev/null 2>&1 || : > "$ROOT/disabled"' HUP INT TERM
    rc=0
    wait "$child" || rc=$?
    trap - HUP INT TERM
    mv "$STATE/result.pending" "$STATE/result.json"
    if [ "$rc" = 0 ] && grep '"cleanup_verified":true' "$STATE/result.json" >/dev/null; then
        rmdir "$STATE/lock"
    else
        : > "$ROOT/disabled"
        echo 'Cleanup unverified: disabled; lock and evidence retained' >&2
        exit 2
    fi
    ;;
stop)
    stop_worker
    ;;
disable)
    # Attempt cooperative removal first; never claim an uncertain stop succeeded.
    rc=0
    stop_worker || rc=2
    : > "$ROOT/disabled"
    [ "$rc" = 0 ] || { echo 'Disabled future starts; current cleanup unverified' >&2; exit 2; }
    ;;
*) exit 64;;
esac
