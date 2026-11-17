> Current next attempt: [factory-managed one-use boot trial](FACTORY-BOOT-TRIAL.md). Native drawing/cleanup passed; live PID replacement failed and is retired. The new boot gate is built and rehearsed offline, not yet accepted on the car. Unattended v1 remains unapproved.

# Startup and rollback contract

Offline-tested management candidate; not an installed unattended service.

Project root proposed: /var/opt/supra-hud. RAM state: /tmp/supra-hud. Confirm the persistent destination, filesystem and startup invocation on the actual unit before use. No installer mounts filesystems, guesses a factory restart, or registers a startup entry.

`deployment/hud-service.sh ROOT STATE startup` enters standby only. `start-parked --guidance-stopped-and-parked` requires enabled state, matching release.ok and a fresh operator assertion. It runs the bounded worker. Duplicate/stale state is refused. `stop` uses the CLEAN handshake rather than killing a PID; uncertain cleanup retains evidence and disables future starts. `disable` attempts cleanup and leaves the disable file even if cleanup fails.

`deployment/switch-release.sh ROOT STATE activate HEX` or `rollback` stops first, refuses uncertain stop, changes the project-owned release pointer and leaves the selected release disabled. The previous pointer supports reverting to the prior release. A release.ok marker is an explicit acceptance decision, not something the build emits. Never mark a release accepted simply to bypass a failed test.

`deployment/factory-controller-wrapper.sh` preserves argv and working directory and execs the original factory binary. It passes through unless the selected release, acceptance marker and factory-hook.enabled match and no disable flag exists. Existing LD_PRELOAD is not overwritten. It is an unregistered candidate until the real startup entry is reviewed. A disable flag makes the loaded hook pass factory traffic through; it does not unload the library.

`tools/release_transaction.py` creates exact-byte apply/rollback scripts for the reviewed supported startup file. Both require the expected current bytes, preserve file permissions, lock their transaction and replace atomically. Rollback refuses to overwrite an independent edit. Keep original bytes and generated rollback locally and on Drive before applying. Restore config AND restart the controller using a verified recovery method to unload an experimental hook. Project release rollback alone cannot do that.

The startup preflight reads starter.cfg, preloader-job-hu.cfg, Appstarter.ini and the boot script plus identity/interfaces/routes/processes/mounts. No configuration is changed. The currently captured Appstarter.ini does not identify the controller launch entry; this is why an exact production patch has not been fabricated offline.

Remaining unattended requirements: real factory interception/ordering proof, authoritative navigation-idle admission after reboot, automatic resume policy, sustained runtime and approved thresholds. Until these pass, boot is standby and display runs are parked/bounded. See ONE-CAR-SESSION-V1.md for ordered acceptance and recovery.
