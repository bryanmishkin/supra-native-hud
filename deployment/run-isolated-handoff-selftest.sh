#!/bin/sh
# Run only from a temporary, verified package on the QNX head unit.
# Never preload the factory controller. This process links a fake provider.
set -eu
cd "${0%/*}"
[ "$(uname -s)" = QNX ] || { echo 'QNX target only' >&2; exit 2; }
case "$PWD" in /tmp/*|/fs/ram5/*) ;; *) echo 'Use a private temporary /tmp directory' >&2; exit 2;; esac
export LD_LIBRARY_PATH="$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_PRELOAD="$PWD/libsupra-navigation-handoff-experimental.so"
exec ./supra-handoff-isolated-selftest-qnx "$PWD/isolated-handoff-$$.sock"
