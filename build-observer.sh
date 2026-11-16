#!/bin/sh
set -eu
cd "$(dirname "$0")"
: "${QNX_HOST:?Set QNX_HOST to the licensed SDK host directory}"
: "${QNX_TARGET:?Set QNX_TARGET to the matching target directory}"
export QNX_HOST QNX_TARGET
qcc="$QNX_HOST/usr/bin/qcc"
test -x "$qcc" || { echo "Missing licensed QNX compiler: $qcc" >&2; exit 1; }
mkdir -p build
"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -O2 \
  -Ivendor/nbt/src -Isrc src/registry_observer.cpp vendor/nbt/src/most/client.cpp \
  vendor/nbt/src/dsi_client.cpp -lsocket -o build/supra-registry-observer-qnx
printf '%s\n' 'Built candidate only; ABI/runtime review required before live use.'
"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -O2 \
  -Isrc -c src/hud_core.cpp -o build/hud_core.o
printf '%s\n' 'Built transport-independent HUD core object.'
"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -O2 \
  -Ivendor/nbt/src -Isrc -c src/native_backend.cpp -o build/native_backend.o
printf '%s\n' 'Built native command encoder object only; no live sender or validated Supra profile.'
"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -O2 \
  -Ivendor/nbt/src -Isrc -c src/native_session.cpp -o build/native_session.o

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -O2 \
  -Ivendor/nbt/src -Isrc src/hud_core.cpp src/native_backend.cpp src/native_session.cpp src/hud_app.cpp \
  tools/hud_pipeline_replay.cpp -o build/supra-hud-offline-replay-qnx
printf '%s\n' 'Built offline replay executable; no live vehicle sender or installation.'

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 \
  -Ivendor/nbt/src -Isrc src/hud_core.cpp src/native_backend.cpp src/native_session.cpp src/hud_app.cpp \
  tools/hud_selftest.cpp -o build/supra-hud-selftest-qnx
printf '%s\n' 'Built bounded no-vehicle-I/O target self-test.'

"$qcc" -V4.4.2,gcc_ntoarmv7le -Wall -Wextra -Werror -O2 \
  tools/hud_passive_capture.c -lpcap -lsocket -o build/supra-passive-capture-qnx
printf '%s\n' 'Built bounded passive capture candidate; target BPF availability must be checked.'

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 \
  -Isrc -c src/someip_model.cpp -o build/someip_model.o
printf '%s\n' 'Built observed-model decoder object; no live transport or ownership granted.'

"$qcc" -V4.4.2,gcc_ntoarmv7le -Wall -Wextra -Werror -O2 \
  tools/hud_continuous_capture.c -lpcap -lsocket -o build/supra-continuous-capture-qnx
printf '%s\n' 'Built 120-second all-port cluster and service-discovery recorder; no deployment.'

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 \
  -Isrc src/hud_core.cpp src/tach_bitmap.cpp tools/tach_bitmap_demo.cpp -o build/supra-tach-bitmap-demo-qnx
printf '%s\n' 'Built synthetic tachometer bitmap generator; no vehicle I/O.'

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 -Isrc -c src/rpm_input.cpp -o build/rpm_input.o

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 \
  -Isrc src/hud_core.cpp src/tach_bitmap.cpp src/standalone_wire.cpp src/navigation_guard.cpp tools/supra_standalone.cpp \
  -lpcap -lsocket -o build/supra-standalone-parked-qnx
printf '%s\n' 'Built direct standalone parked candidate with passive factory-activity revocation; no autostart.'

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 -shared -fPIC \
  tools/navigation_handoff_hook.cpp -lsocket -o build/libsupra-navigation-handoff-experimental.so
printf '%s\n' 'Built experimental pre-send handoff hook. Not loaded into any factory process.'

"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 -shared -fPIC \
  tests/handoff_fake_factory.cpp -o build/libsupra-fake-factory-test.so
"$qcc" -V4.4.2,gcc_ntoarmv7le_gpp -lang-c++ -Wc,-std=gnu++98 -Wall -Wextra -Werror -O2 \
  tests/handoff_target_selftest.cpp -Lbuild -lsupra-fake-factory-test -lsocket -o build/supra-handoff-isolated-selftest-qnx
printf '%s\n' 'Built fake-factory handoff self-test; never attaches to a factory process.'
