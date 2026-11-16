#!/bin/sh
# Read-only targeted preflight. Save privately; may include proprietary config.
set -eu
uname -a
printf '\n--- interfaces ---\n'
/sbin/ifconfig -a
printf '\n--- routes ---\n'
netstat -rn
printf '\n--- processes ---\n'
pidin ar
printf '\n--- mounts ---\n'
mount
for path in /opt/sys/etc/starter.cfg /opt/sys/etc/preloader-job-hu.cfg /opt/nav/eceusa/bin/Appstarter.ini /proc/boot/.script; do
    printf '\n--- FILE %s ---\n' "$path"
    if [ -f "$path" ]; then ls -ln "$path"; dd if="$path" bs=4096 count=129; else echo MISSING; fi
    printf '\n--- END FILE ---\n'
done
