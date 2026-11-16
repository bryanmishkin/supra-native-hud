#!/bin/sh
# Uses only local loopback servers and a previously prepared private profile.
set -eu
[ "$#" = 2 ] || { echo 'usage: test-standalone-offline.sh PROFILE NEW_OUTPUT_DIRECTORY' >&2; exit 64; }
PROFILE=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
mkdir "$2"
OUT=$(cd "$2" && pwd)
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
CXX=${CXX:-c++}
"$CXX" -std=c++98 -Wall -Wextra -Werror -DSUPRA_TEST -Isrc \
 src/hud_core.cpp src/tach_bitmap.cpp src/standalone_wire.cpp src/navigation_guard.cpp \
 tools/supra_standalone.cpp -lpcap -o "$OUT/standalone-host-test"
"$CXX" -std=c++98 -Wall -Wextra -Werror -Isrc src/navigation_guard.cpp tests/test_navigation_guard.cpp -o "$OUT/navigation-guard-test"
"$OUT/navigation-guard-test"
python3 tests/standalone_integration.py "$OUT/standalone-host-test" "$PROFILE" "$OUT/integration"
