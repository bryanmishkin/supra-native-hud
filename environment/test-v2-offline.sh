#!/bin/sh
# Only loopback peers and synthetic/captured replay values. No vehicle connection.
set -eu
[ "$#" = 2 ] || { echo 'usage: test-v2-offline.sh PROFILE NEW_OUTPUT_DIRECTORY' >&2; exit 64; }
PROFILE=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
mkdir "$2"; OUT=$(cd "$2" && pwd)
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
CXX=${CXX:-c++}
"$CXX" -std=c++98 -Wall -Wextra -Werror -Isrc src/hud_core.cpp tests/test_boost_input.cpp -o "$OUT/boost-input"
"$OUT/boost-input"
"$CXX" -std=c++98 -Wall -Wextra -Werror -Isrc src/hud_core.cpp src/tach_bitmap.cpp tests/test_tach_bitmap.cpp -o "$OUT/bitmap"
"$OUT/bitmap"
"$CXX" -std=c++98 -Wall -Wextra -Werror -DSUPRA_TEST -Isrc src/hud_core.cpp src/tach_bitmap.cpp src/standalone_wire.cpp src/navigation_guard.cpp tools/supra_standalone.cpp -lpcap -o "$OUT/worker"
python3 tests/v2_integration.py "$OUT/worker" "$PROFILE" "$OUT/integration"
python3 tests/standalone_integration.py "$OUT/worker" "$PROFILE" "$OUT/v1-regression"
