#!/bin/sh
# Separate candidate only. Does not rebuild or replace the V1 worker.
set -eu
[ "$#" = 2 ] || { echo 'Usage: build-corrected-pip.sh captured-libscreen.so.1 new-output-directory' >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
LIB=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
test -f "$LIB"
test ! -e "$2"
mkdir -p "$2"
OUT=$(cd "$2" && pwd)
docker run --rm --platform linux/amd64 --network none \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$ROOT,dst=/source,readonly" \
  --mount "type=bind,src=$LIB,dst=/target/libscreen.so,readonly" \
  --mount "type=bind,src=$OUT,dst=/out" \
  --env QNX_CONFIGURATION=/etc/qnx \
  "${QNX_BUILD_IMAGE:-supra-qnx650-build:local}" sh -c '
    set -eu
    cp /source/tools/pip/corrected/window_marker.cpp /tmp/window_marker.cpp
    "$QNX_HOST/usr/bin/qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ \
      -Wc,-std=gnu++0x -Wall -Wextra -Werror -O2 \
      -I/source/tools/pip/corrected -I/source/tools/pip/include -I/source/vendor/ryseek-pip \
      /tmp/window_marker.cpp -L/target -Wl,-rpath,/usr/lib:/lib \
      -lscreen -lsocket -o /out/supra-pip-corrected-marker-qnx

  '
echo 'Built separate experimental producer; no vehicle connection or deployment.'
