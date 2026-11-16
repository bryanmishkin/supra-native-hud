#!/bin/sh
set -eu
cd /workspace
mkdir -p /tmp/supra-tests
for bits in 64 32; do
  g++ -m$bits -std=gnu++98 -Wall -Wextra -Werror -Isrc src/hud_core.cpp src/tach_bitmap.cpp tests/test_tach_bitmap.cpp -o /tmp/supra-tests/tach-bitmap-$bits
  /tmp/supra-tests/tach-bitmap-$bits
  g++ -m$bits -std=gnu++98 -Wall -Wextra -Werror -Ivendor/nbt/src -Isrc src/hud_core.cpp src/native_backend.cpp src/native_session.cpp src/hud_app.cpp tests/test_hud_app.cpp -o /tmp/supra-tests/hud-app-$bits
  /tmp/supra-tests/hud-app-$bits
  g++ -m$bits -std=gnu++98 -Wall -Wextra -Werror -Ivendor/nbt/src -Isrc src/hud_core.cpp src/native_backend.cpp src/native_session.cpp src/hud_app.cpp tools/hud_selftest.cpp -o /tmp/supra-tests/selftest-$bits
  /tmp/supra-tests/selftest-$bits --self-test
  g++ -m$bits -std=gnu++98 -Wall -Wextra -Werror -Ivendor/nbt/src -Isrc src/hud_core.cpp src/native_backend.cpp src/native_session.cpp tests/test_native_session.cpp -o /tmp/supra-tests/native-session-$bits
  /tmp/supra-tests/native-session-$bits
  g++ -m$bits -std=gnu++98 -Wall -Wextra -Werror -Ivendor/nbt/src -Isrc src/hud_core.cpp src/native_backend.cpp tests/test_native_backend.cpp -o /tmp/supra-tests/native-backend-$bits
  /tmp/supra-tests/native-backend-$bits
  g++ -m$bits -std=gnu++98 -Wall -Wextra -Werror -Ivendor/nbt/src tests/test_dsi_payload.cpp -o /tmp/supra-tests/dsi-payload-$bits
  /tmp/supra-tests/dsi-payload-$bits
  g++ -m$bits -std=gnu++98 -Wall -Wextra -Werror -Isrc src/hud_core.cpp tests/test_hud_core.cpp -o /tmp/supra-tests/hud-core-$bits
  /tmp/supra-tests/hud-core-$bits
  g++ -m$bits -std=gnu++98 -Wall -Wextra -pthread \
    -Ivendor/nbt/src -Ivendor/nbt/tests -Isrc \
    tests/test_registry_observer.cpp vendor/nbt/src/most/client.cpp vendor/nbt/tests/fake_dsi_client.cpp \
    -o /tmp/supra-tests/registry-$bits
  /tmp/supra-tests/registry-$bits
  g++ -m$bits -std=gnu++98 -Wall -Wextra -pthread \
    -Ivendor/nbt/src -Isrc src/registry_observer.cpp vendor/nbt/src/most/client.cpp \
    vendor/nbt/src/dsi_client.cpp -ldl -o /tmp/supra-tests/observer-$bits
  file /tmp/supra-tests/observer-$bits
 done
python3 -m unittest discover -s tests -p 'test_*.py' -v
