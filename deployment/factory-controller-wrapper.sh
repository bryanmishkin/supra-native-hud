#!/bin/sh
# Candidate launch adapter only. Factory executable and argv are preserved.
# Registering this in the factory starter requires current-target review/testing.
ROOT=/var/opt/supra-hud
STATE=/tmp/supra-hud
FACTORY=/opt/nav/eceusa/bin/NavNBTEvoController
release=''
if [ -f "$ROOT/current" ]; then release=$(cat "$ROOT/current"); fi
case "$release" in ''|*[!0-9a-f]*) exec "$FACTORY" "$@";; esac
DIR="$ROOT/releases/$release"
if [ -f "$ROOT/disabled" ] || [ ! -f "$ROOT/factory-hook.enabled" ] || \
   [ ! -f "$DIR/release.ok" ] || [ ! -r "$DIR/libsupra-navigation-handoff-experimental.so" ]; then
    exec "$FACTORY" "$@"
fi
if [ "$(cat "$DIR/release.ok")" != "$release" ] || \
   [ "$(cat "$ROOT/factory-hook.enabled")" != "$release" ]; then
    exec "$FACTORY" "$@"
fi
# Do not replace or guess how to combine an existing factory preload setting.
if [ -n "${LD_PRELOAD:-}" ]; then exec "$FACTORY" "$@"; fi
export SUPRA_HUD_HANDOFF="$STATE/active.jsonl.handoff"
export SUPRA_HUD_DISABLE_FILE="$ROOT/disabled"
export LD_PRELOAD="$DIR/libsupra-navigation-handoff-experimental.so"
exec "$FACTORY" "$@"
