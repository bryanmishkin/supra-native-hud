#!/bin/sh
set -eu
: "${QNX_SDK_DIR:?Point QNX_SDK_DIR at an installed, licensed full QNX SDP 6.5 Linux SDK}"
SDK=$(cd "$QNX_SDK_DIR" && pwd)
ROOT=$(cd "$(dirname "$0")/.." && pwd)
test -x "$SDK/host/linux/x86/usr/bin/qcc" || { echo 'SDK is missing the Linux qcc driver' >&2; exit 2; }
test -d "$SDK/target/qnx6/armle-v7" || test -d "$SDK/target/qnx6/armle" || { echo 'Full ARM target SDK required; x86-only is insufficient' >&2; exit 2; }
set --
# A valid, vendor-activated configuration can be supplied separately from the SDK.
# Never package license material with the project or attempt activation here.
if [ -n "${QNX_LICENSE_DIR:-}" ]; then
  LICENSE_DIR=$(cd "$QNX_LICENSE_DIR" && pwd)
  set -- --mount "type=bind,src=$LICENSE_DIR,dst=/qnx-license,readonly" \
    --env QNX_CONFIGURATION=/qnx-license
fi
CONTAINER=$(docker create --platform linux/amd64 --network none \
  --cap-drop ALL --security-opt no-new-privileges "$@" \
  --mount "type=bind,src=$SDK,dst=/opt/qnx650,readonly" \
  --mount "type=bind,src=$ROOT,dst=/source,readonly" \
  supra-hud-build-host:22.04 sh -c \
  'set -eu; cp -R /source /tmp/current-build; cd /tmp/current-build; sh ./build-observer.sh')
trap 'docker rm -f "$CONTAINER" >/dev/null' EXIT HUP INT TERM
docker start -a "$CONTAINER"
STATUS=$(docker inspect --format '{{.State.ExitCode}}' "$CONTAINER")
[ "$STATUS" = 0 ] || exit "$STATUS"
mkdir -p "$ROOT/build"
docker cp "$CONTAINER:/tmp/current-build/build/." "$ROOT/build/"
