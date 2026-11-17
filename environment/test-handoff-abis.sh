#!/bin/sh
set -eu
mkdir -p /tmp/hook-abi
for abi in nav hmi; do
 out=/tmp/hook-abi/$abi
 mkdir -p "$out"
 cp /source/tests/handoff_fake_factory.cpp "$out/fake.cpp"
 cp /source/tests/handoff_hook_driver.cpp "$out/driver.cpp"
 if [ "$abi" = hmi ]; then
  sed -i 's/RK8TWeakPtr/RKSt8weak_ptr/g' "$out/fake.cpp" "$out/driver.cpp"
 fi
 g++ -std=c++98 -Wall -Wextra -Werror -fPIC -shared /source/tools/navigation_handoff_hook.cpp -ldl -lpthread -o "$out/libhandoff.so"
 g++ -std=c++98 -fPIC -shared "$out/fake.cpp" -o "$out/libfake.so"
 g++ -std=c++98 "$out/driver.cpp" -L"$out" -lfake -Wl,-rpath,"$out" -o "$out/hook-driver"
 SUPRA_TEST_ROLE="$abi" python3 /source/tests/handoff_hook_integration.py "$out"
done
