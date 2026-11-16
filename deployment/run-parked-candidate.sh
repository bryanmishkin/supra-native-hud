#!/bin/sh
# Bounded candidate only; no installation or automatic startup.
set -eu
[ "${1:-}" = '--guidance-stopped-and-parked' ] || { echo 'Requires current parked/stopped-guidance confirmation' >&2; exit 64; }
[ "$#" = 2 ] || { echo 'Supply a new absolute journal path as the second argument' >&2; exit 64; }
case "$2" in /tmp/*|/fs/ram5/*) ;; *) echo 'Journal must be inside temporary RAM storage' >&2; exit 64;; esac
cd "${0%/*}"
[ "$(uname -s)" = QNX ] || exit 2
case "$PWD" in /tmp/*|/fs/ram5/*) ;; *) echo 'Use a private temporary /tmp directory' >&2; exit 2;; esac
# Current saved topology; confirm at session preflight. No Mac/SSH runtime dependency.
exec ./supra-standalone-parked-qnx --parked-guidance-stopped ./supra-profile.bin \
  169.254.199.119 169.254.106.96 160.48.199.96 vlan73 30 "$2"
