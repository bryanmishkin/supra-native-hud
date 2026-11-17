# Next attempt: factory-managed, one-use hook trial

Prepared offline after the failed live replacement tests. This is a concrete parked integration test, not a production v1 installer. Never stop/replace the running controller PID and never disable factory watchdogs.

## Evidence behind the change

The saved QNX core is PID 225334 (the original controller), SIGSEGV. The crash context is consistent with libc `_list_release` called by `__free`; the main thread is in `pthread_join`. Symbol labels depend on the captured libc/load-base match; PID/signal are directly recorded by the core and independently read by QNX GDB. The watchdog snapshot names the old PID while replacement PID 1441846 and its threads are running. This supports a shutdown/supervision failure, not a proven crash in the hooked replacement. Exact system reset policy is not established by the dump alone.

The previous ad-hoc supervisor did not provide reliable recovery across a full head-unit restart. It is retired. Existing factory watchdogs remain enabled and unchanged.

## New design and recovery

Factory `NavigationEceUsa.cfg` keeps the same process number, dependencies, environment, working directory, arguments and scheduling partition. Only its controller executable entry points to `supra-boot-trial-gate-qnx` next to the original executable in `/opt/nav/eceusa/bin`. The small native gate execs the original controller in the SAME PID. Placing it on the same filesystem as the original avoids introducing a new boot-mount dependency for basic factory operation.

Default is original factory behavior. `/var/opt/supra-hud/boot-trial/armed` must contain an exact explicit ticket to load the hook once. The gate atomically creates a consumed ticket, removes the armed ticket and syncs before executing with the hook. Missing, malformed, disabled, insecure or already-consumed state falls back to the original controller. An inherited factory LD_PRELOAD is preserved and prevents experimental activation. Missing `/var` state also falls back. Nothing starts the tachometer at boot.

If a hooked boot fails, do not arm again. The following normal boot uses the original controller because the ticket was consumed. This is a designed fallback, NOT a target-validated guarantee yet. We test the unarmed gate first. The original config is also preserved as a hard link on its own filesystem; the native rollback restores its original inode, permissions and bytes. No shell cmp/sync/dirname/printf dependency remains in this transaction.

## Kit and exact operator sequence

Use `tools/boot_trial_session.py` from the Mac with a verified SSH master. Each invocation uses `--execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET"`. OUT is a new private session directory. Default without --execute only prints the plan and does not contact the car.

1. `preflight`: verify current QNX identity, exactly one original controller and exact before-config bytes. Save current evidence to Drive before applying configuration. Abort if the startup file differs; regenerate/review from current bytes rather than overwriting a change.
2. `rehearse`: creates an exclusive RAM fixture. Runs the ARM transaction helper on fixture files (apply and inode-preserving rollback) and the native boot gate against a FAKE factory executable (default, armed once, consumed next invocation). No factory process is touched. A failure stops the session before startup changes.
3. `configure`: exclusively stage and read-back-verify the native gate, hook and original/replacement configs; apply the single-entry config change with the native transaction helper. No arm ticket is created. The current controller continues running.
4. Perform a normal user-controlled head-unit shutdown/restart while parked. Do not signal the controller, launch another starter or run a forced process-kill command. The user must have a working normal restart method before step 3; otherwise stop before configuring. Reconnect temporary SSH as necessary.
5. Confirm factory HUD, radio, navigation and iDrive normal, then `verify-baseline --factory-normal`. Require the RAM boot-boundary marker to be gone, no hook mapping, unchanged candidate config and TWO MINUTES of stable process checks. This tests the gate under real factory supervision with the hook off.
6. `arm --factory-normal`: rechecks the same baseline controller, exact gate/hook bytes, config and ticket state, then writes the one-use ticket. Perform the same normal restart. Do not remove/overwrite a consumed ticket to force another attempt.
7. Confirm factory functions normal, then `verify-hook --factory-normal`. Require the RAM boot-boundary marker to be gone, a stable controller PID, hook mapped, arm ticket absent and consumed ticket correct. Observe TWO MINUTES without restarting or drawing. If this fails, the next normal boot is unarmed; restore config when access is available. Do not repeat an unexplained failure.
8. With guidance stopped and normal HUD confirmed, stage the proven standalone worker, private profile and native control client in a NEW `/tmp/supra-hud-boottrial` directory with byte-for-byte readback. The hook endpoint is fixed to `/tmp/supra-hud-boottrial/active.jsonl.handoff`. Start the exact parked worker:

```
/tmp/supra-hud-boottrial/supra-standalone-parked-qnx \
  --parked-guidance-stopped /tmp/supra-hud-boottrial/supra-profile.bin \
  169.254.199.119 169.254.106.96 160.48.199.96 vlan73 30 \
  /tmp/supra-hud-boottrial/active.jsonl
```

As soon as the tachometer is visible, ask the user to START FACTORY GUIDANCE during the same 30-second window. Success requires the worker to exit for `factory_navigation_request` with cleanup/resource absence true; the persistent `handoff.log` must show CLEAN before FACTORY_SEND for the factory controller; navigation must then display normally in windshield and cluster. A passive quiesce, timeout, or externally requested stop is NOT a navigation-handoff pass. No revving needed.

9. Preserve the journal, result and handoff log before another run. Only after clean removal and guidance stopped may a fresh journal run test radio activity. Radio may originate from another process: if it is not intercepted before sending, record failure; do not expand injection into other processes during the same experiment. No automatic resume is implemented.
10. With no active worker/socket and both displays clear, `rollback` restores the original config inode and bytes. It intentionally remains callable after a partial configuration attempt; if exact-image checks refuse, inspect preserved backup/target rather than overriding the guard. Restoring config does not unload a running hook. Perform one final normal restart, confirm factory functions, then `verify-restored --factory-normal` (RAM boot-boundary marker gone, stable PID, no hook, exact original config, two-minute stability).
11. Save and verify all evidence in Drive before unplugging. Remove only the specifically staged project files after confirming the original config is restored and no hook/worker is running; retain original-inode evidence. Closing SSH does not disable vehicle SSH.

## Boundaries

The gate preserves default factory operation; it does not grant permission to draw. Automatic idle detection/resume, sustained runtime and final shift thresholds remain separate product work. This next attempt is ready for staged validation only. No claim is made that unattended installation or a dinner-drive test will pass.

Approximate occupied time: three normal head-unit restarts plus three two-minute stability windows, the live handoff checks and final recovery. Keep time for failure analysis. If any boot fails, recover first; do not rush to driving with an experimental hook or unresolved display state.

Boot identity is not inferred from a changed PID: factory PIDs can repeat. The runner places a unique RAM-only sentinel before each requested restart and requires it to disappear, then checks the resulting controller for two minutes. This relies on the /tmp RAM filesystem behavior verified by both actual head-unit restarts in the prior session.
