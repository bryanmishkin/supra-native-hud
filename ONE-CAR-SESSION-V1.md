> Live validation supersedes earlier readiness claims: [results and failed startup integration](docs/v1-native-validation-2026-11-16.md). Native drawing/cleanup passed; controller replacement caused restarts. No unattended installation is accepted. Do not repeat the restart trial.

# One-session v1 acceptance — 2026-11-16

Status: executable RAM acceptance kit ready; unattended installation is NOT yet accepted. Previously proven sport UI/color correction is retained. No vehicle changes were made during this offline preparation.

## Before the session

Bring the verified qnx-validation-kit, this source checkout, existing SSH access, and enough time to keep the car connected through failure analysis. Park outdoors. Start with guidance stopped and radio selector closed. Do not rev for color tests. Preserve a working recovery connection throughout any factory startup change.

## Ordered executable acceptance

Use tools/run_v1_validation.py from the Mac. Set KIT to the absolute kit directory, OUT to a new private evidence directory, and SOCKET to the existing authenticated SSH master socket. Every command uses the same values:

```
python3 tools/run_v1_validation.py preflight --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET"
python3 tools/run_v1_validation.py stage --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET"
python3 tools/run_v1_validation.py isolated --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET"
python3 tools/run_v1_validation.py rpm --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET"
```

Preflight must identify QNX hu-omap 6.5.0 armle and save actual startup configuration. Review the routing and current process arguments against the captured topology. Stage verifies every uploaded byte. Isolated must report native loader self-check and fake-factory hook ABI/CLEAN success; it does not load into the factory controller. RPM must return 40 valid readings with no HUD writes; compare with the factory idle tachometer. Stop if routing, identity, ABI or readings disagree.

After a fresh visual confirmation that guidance is stopped and the normal HUD is visible:

```
python3 tools/run_v1_validation.py draw --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET" --guidance-stopped
```

Observe 30 seconds: readable larger digits and bar, measured RPM agreeing with factory, no flashing/circle/arrow/clipping. Require cleanup_verified, shared_instance_preserved, and graphics absent from BOTH displays. A retry gets a new journal; never overwrite failed evidence.

Repeat the fresh stopped-guidance confirmation, then:

```
python3 tools/run_v1_validation.py yield --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET" --guidance-stopped
```

This requests cooperative removal after five seconds using the native control client. Require factory_navigation_request plus verified cleanup, then visual absence. This proves the handoff mechanism, NOT automatic interception of real navigation.

## Conditional factory integration in this same session

1. Read the precise starter/controller launch entry saved by preflight. Save original bytes, permissions, process arguments and mount state locally and to Drive before changing anything. Captured Appstarter.ini alone does not contain the controller entry. Do not guess a restart command or boot path.
2. Review a minimal startup edit that invokes deployment/factory-controller-wrapper.sh while preserving the original working directory and every argument. Generate apply/rollback with tools/release_transaction.py using the exact before/after bytes and supported target. Rehearse the pair on a copy before touching the target. The wrapper defaults to factory passthrough; enabling it is a separate, release-bound decision.
3. Only with a verified controller restart/recovery method and saved rollback, test factory startup with the disabled wrapper, then the enabled hook. Confirm the real hook is loaded and executes before the relevant factory send. The isolated fake-factory test is insufficient evidence here.
4. While the native tachometer is active, start real factory guidance: custom cleanup must finish BEFORE the factory model is sent; navigation must render correctly in windshield and cluster. Repeat with radio activity. Save ordering evidence and visual observations. An external control-client yield does not satisfy this gate.
5. Test disable during active drawing: cleanup and resource absence must pass, no restart should occur. Test release rollback; selection remains disabled. Restore original startup bytes, restart through the verified factory mechanism, and prove the experimental library is no longer loaded. Check normal HUD, radio, navigation and iDrive.
6. Repeat the intended restart cycle with guidance already active and inactive. Startup must stay in standby unless an authoritative idle policy has been implemented and tested. Never treat a quiet packet interval or reboot as proof that navigation is stopped.
7. Before an unattended v1 designation, implement/test longer runtime, shutdown and recovery, and agree vehicle-appropriate shift thresholds. Current worker is deliberately limited to 30 seconds and has no automatic resume. These are real remaining product gates, not waived by installation.

Use tools/validation_session.py to record evidence and observations against the kit hash. It is a manual acceptance ledger; recording a gate is not a substitute for performing it. Repeating an earlier gate invalidates dependent gates. Do not issue release.ok or enable unattended operation based only on host tests.

## Before unplugging

```
python3 tools/run_v1_validation.py collect --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET"
```

Inspect all journals, final results, known resource absence and cleanup. Confirm both displays are normal, then test real factory navigation in both, stop guidance, test radio and iDrive. Save evidence to Drive and verify upload. Only after both executable draw/yield phases pass and the visual checks are current:

```
python3 tools/run_v1_validation.py remove --execute --kit "$KIT" --output "$OUT" --ssh-socket "$SOCKET" --visual-cleanup-confirmed
```

Removal refuses active sockets and failed runs; preserve their evidence and investigate while still connected. Unknown files are not recursively erased. Persistent configuration/hook rollback is separate from this RAM-kit removal. Do not unplug with unresolved custom graphics or an unverified factory restore.
