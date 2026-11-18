#!/bin/sh
set -eu
[ "$#" = 2 ] || exit 64
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PROFILE=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
mkdir "$2"; OUT=$(cd "$2" && pwd)
cd "$ROOT"
COMMON='src/hud_core.cpp src/tach_bitmap.cpp src/standalone_wire.cpp src/navigation_guard.cpp'
c++ -std=c++98 -Wall -Wextra -Werror -DSUPRA_TEST -Isrc $COMMON tools/supra_standalone.cpp -lpcap -o "$OUT/worker"
c++ -std=c++98 -Wall -Wextra -Werror -DSUPRA_TEST -Isrc $COMMON src/factory_lease.cpp src/factory_stream.cpp tools/supra_resident.cpp -lpcap -o "$OUT/resident"
c++ -std=c++98 -Wall -Wextra -Werror -Isrc src/factory_lease.cpp tests/test_factory_lease.cpp -o "$OUT/lease-test"
c++ -std=c++98 -Wall -Wextra -Werror -Isrc src/factory_lease.cpp src/factory_stream.cpp tests/test_factory_stream.cpp -o c++ -std=c++98 -Wall -Wextra -Werror -Isrc -Ivendor/nbt/src src/hud_core.cpp src/tach_bitmap.cpp tests/test_worker_outcome.cpp -o "$OUT/outcome-test"
c++ -std=c++98 -Wall -Wextra -Werror -DSUPRA_TEST -Isrc $COMMON src/factory_lease.cpp src/factory_stream.cpp tests/test_fault_retention.cpp -lpcap -o "$OUT/retention-test"
"$OUT/retention-test"
"$OUT/outcome-test"
"$OUT/stream-test"
"$OUT/stream-test"
"$OUT/lease-test"
python3 tests/resident_integration.py "$OUT/resident" "$OUT/worker" "$PROFILE" "$OUT/results.json"
python3 tests/resident_startup_deadline.py "$OUT/resident" "$OUT/worker" "$PROFILE" "$OUT/startup-watchdog.json"

python3 tests/pool_retry_integration.py "$OUT/resident" "$OUT/worker" "$PROFILE" "$OUT/pool-retry.json"

python3 tests/factory_bitmap_coexistence.py "$OUT/worker" "$PROFILE" "$OUT/factory-coexistence.json"
