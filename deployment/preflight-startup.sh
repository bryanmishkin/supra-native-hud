#!/bin/sh
# Read-only targeted preflight. Save privately; may include proprietary config.
set -eu
uname -a
echo '--- interfaces ---'
/sbin/ifconfig -a
echo '--- routes ---'
netstat -rn
echo '--- processes ---'
pidin ar
echo '--- mounts ---'
mount
for path in /opt/sys/etc/starter.cfg /opt/sys/etc/preloader-job-hu.cfg /opt/nav/eceusa/bin/Appstarter.ini /proc/boot/.script; do
    echo "--- FILE $path ---"
    if [ -f "$path" ]; then ls -ln "$path"; dd if="$path" bs=4096 count=129; else echo MISSING; fi
    echo '--- END FILE ---'
done
