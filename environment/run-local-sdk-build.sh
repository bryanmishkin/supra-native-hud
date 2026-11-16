#!/bin/sh
# Uses the locally preserved SDK image; do not publish that image or license material.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
IMAGE=${QNX_BUILD_IMAGE:-supra-qnx650-build:local}
CONTAINER=$(docker create --platform linux/amd64 --network none \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$ROOT,dst=/source,readonly" \
  --env QNX_CONFIGURATION=/etc/qnx "$IMAGE" sh -c \
  'set -eu; cp -R /source /tmp/current-build; cd /tmp/current-build; sh ./build-observer.sh')
trap 'docker rm -f "$CONTAINER" >/dev/null' EXIT HUP INT TERM
docker start -a "$CONTAINER"
STATUS=$(docker inspect --format '{{.State.ExitCode}}' "$CONTAINER")
[ "$STATUS" = 0 ] || exit "$STATUS"
mkdir -p "$ROOT/build"
docker cp "$CONTAINER:/tmp/current-build/build/." "$ROOT/build/"
printf '%s\n' 'Candidates saved in build/. No vehicle deployment performed.'
