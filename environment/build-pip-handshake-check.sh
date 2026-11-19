#!/bin/sh
# Compile only: the produced executable allows loopback, never vehicle addresses.
set -eu
[ "$#" = 1 ] || { echo 'Usage: build-pip-handshake-check.sh new-output-directory' >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
test ! -e "$1"
mkdir -p "$1"
OUT=$(cd "$1" && pwd)
docker run --rm --platform linux/amd64 --network none \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$ROOT,dst=/source,readonly" \
  --mount "type=bind,src=$OUT,dst=/out" \
  --env QNX_CONFIGURATION=/etc/qnx \
  "${QNX_BUILD_IMAGE:-supra-qnx650-build:local}" sh -c '
    set -eu
    cp /source/tests/pip_transport_loopback.cpp /tmp/pip_transport_loopback.cpp
    "$QNX_HOST/usr/bin/qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ \
      -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 \
      -I/source/tools/pip/include /tmp/pip_transport_loopback.cpp \
      -lsocket -o /out/pip-handshake-loopback-qnx
  '
