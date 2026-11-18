# Persistent installation and rollback

Current installed identity: [V1 baseline](docs/V1-BASELINE.md). The public compiled release supplies runtime components only; fresh installation still requires the target-specific inputs below. The reference car already has an enabled installation: do not rerun fresh preflight/staging over it. Revision08 records are historical; final runtime upgrades are documented in the baseline's private receipts.

The installed app runs continuously; it is not a 30-second demo. Successful acceptance ends with **commit and leave running**, unless the owner requests removal. Earlier RAM-only runners and one-boot research scripts are not substitutes for this installer.

## Before scheduling car time

Prepare all offline work first. Use a dedicated evidence directory per vehicle/attempt. Keep exact originals, kit hashes and installer state available locally even if the car disconnects.

Required inputs:

- Source revision, QNX ARM build and completed [build/audit checks](environment/README.md).
- Exact original `/opt/nav/eceusa/bin/NavigationEceUsa.cfg` and `/opt/sys/etc/starter.cfg` from the target.
- Exact target `/opt/nav/eceusa/bin/NavNBTEvoController` and `/opt/hmi/bin/zipped/HmiMain3D` for hashing and ABI review.
- Reviewed target runtime libraries, including `/opt/sys/lib/libsys_someip.gpp.so.8`.
- Verified symbol-free `supra-profile.bin`; it is not committed to GitHub. `tools/prepare_native_profile.py SOURCE_TRACE OUTPUT` builds it only from the specific successful static trace structure it validates. Its source JSON uses `awaiting_visual_verification`, so the builder does **not** itself establish that a human confirmed the image. Retain that confirmation separately.
- Python 3 with `pyelftools`, a verified root SSH master connection and saved host identity. The installer does not unlock SSH or install access utilities.
- A known normal iDrive restart method and enough parked time for two trial restarts, handoff checks, at least five uninterrupted minutes, final commit/restart, or recovery.

On the reference car, parked outdoors with engine running was needed to see the HUD. Accessory mode alone did not display it. High-RPM shift-light checks can use simulated display values; no engine-speed command is part of this application.

## Build the private kit

Run from the repository root. Replace the example paths with target-specific inputs; keep private files outside the source checkout or in ignored folders.

```sh
python3 tools/prepare_persistent.py \
  --nav /private/vehicle/NavigationEceUsa.cfg \
  --system /private/vehicle/starter.cfg \
  --build build \
  --profile /private/vehicle/supra-profile.bin \
  --nav-exe /private/vehicle/NavNBTEvoController \
  --hmi-exe /private/vehicle/HmiMain3D \
  --output /private/vehicle/persistent-kit
```

The output must not already exist. It contains eight native components, the profile, original/replacement configurations, file hashes and factory executable hashes. Preparation checks the exact XML process names, partitions, process numbers, and equal `Args`/`ResArgs`; it replaces only the process name bytes. It does not perform a target ELF audit or validate a new vehicle's profile. A generated manifest's legacy `gates_not_yet_target_validated` field lists acceptance obligations for the new kit, not the historical status of the reference car.

## What is installed

| Location | Change |
| --- | --- |
| `/var/opt/supra-hud/v1` | Private release components, profile, configuration backups and activation state |
| `/opt/nav/eceusa/bin/supra-nav-start-qnx` | Nav same-PID startup gate |
| `/opt/hmi/bin/supra-hmi-start-qnx` | HMI same-PID startup gate |
| `/opt/nav/eceusa/bin/NavigationEceUsa.cfg` | Exact nav process-name substitution |
| `/opt/sys/etc/starter.cfg` | Exact HMI process-name substitution |
| `/tmp/supra-hud-v1` | Boot-local resident state, sockets and bounded logs |

The installer briefly remounts `/fs/sda0` writable for startup edits, verifies bytes, and restores read-only protection. It does not flash firmware or code ECUs. Original factory executable bytes are not replaced. The parent `/var/opt/supra-hud` must already exist appropriately; the installer creates only its `v1` child. Inspect and prepare a missing parent deliberately before installation. Do not reuse an existing `v1` directory as a fresh installation.

## Connection and phase commands

Use an already authenticated, host-verified OpenSSH control socket. `Remote` checks that it is a live master; it does not establish a new fallback login. A normal iDrive restart can close SSH, so re-establish the authorized diagnostic connection and master after a restart before collecting evidence.

```sh
KIT=/private/vehicle/persistent-kit
EVIDENCE=/private/vehicle/install-session
SOCKET=/private/vehicle/verified-ssh-master
HEAD=169.254.199.119

# Prints a plan only; it does not contact the vehicle.
python3 tools/persistent_install.py preflight

# Run one phase at a time and review its result before continuing.
python3 tools/persistent_install.py preflight --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD"
```

`EVIDENCE` must be new for preflight. All later phases use the **same** kit, evidence directory, head address and current verified socket. `installer.json` pins the kit and records commands/phases. Do not invoke with `python -O`: the current tool uses assertions for validation. These phases are not a blind retry loop; a failed phase requires inspection of its saved output and target state.

### 1. Preflight

Checks target QNX identity, absence of loaded hooks, exact original startup images, exact factory executable hashes, required live HMI library exports and absence of the release directory. This is read-only. A mismatch stops the installation; do not bypass it.

### 2. Install unarmed

```sh
python3 tools/persistent_install.py install --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD"
```

Stages and reads back files, installs gates, applies exact startup edits and restores read-only protection. No activation token is created. Perform a **normal owner-operated iDrive restart**, then confirm factory HUD/iDrive/navigation/radio are normal and no tachometer/hook is active. Reconnect and verify before arming. Do not kill or manually replace supervised factory processes.

### 3. Arm one trial boot

```sh
python3 tools/persistent_install.py arm --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD"
```

Perform another normal restart with guidance stopped and the radio selector closed. The resident waits at least 30 seconds from its startup and requires committed idle events from both factory lanes. Allow about a minute for normal startup, but do not interpret elapsed time as proof of readiness. A trial token is consumed once; do not delete `consumed` or `disabled` to force another attempt.

### 4. Complete acceptance on this exact candidate

| Check | Required observation and evidence |
| --- | --- |
| Automatic startup | Tach appears without manually launching it or opening/closing factory features to coax admission. Live RPM plausible against factory gauge; no circle/arrow/flashing. Both hooks mapped; resident healthy. |
| Navigation takeover | Start guidance while tach visible. Tach disappears; navigation normal in windshield and cluster. Worker reports verified cleanup. |
| Navigation return | Stop guidance. Tach returns automatically after acknowledged idle, with resident still healthy. |
| Radio takeover/return | Open selector; tach disappears and selector is normal. Let selector close; tach returns. Repeat once. Record clean stop/results for both cycles. |
| Sustained run | Final resumed worker stays uninterrupted for at least five minutes and 1200 frames, with smooth live RPM. Record frame count, monotonic timestamps, unchanged worker-start count and healthy status. |
| Commit | Only after all preceding machine and visual checks pass. |
| Committed restart | Normal restart; tach returns automatically. Recheck radio handoff/return where time permits and record whether it was actually repeated. An unplugged restart confirms no Mac dependency. |

Collect after handoffs and before restarting/unplugging:

```sh
python3 tools/persistent_install.py collect --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD"
```

`collect` overwrites its checkpoint filenames; copy each checkpoint to a separate local subdirectory before the next one. It saves status/results/journals, but not every useful artifact; see [operations evidence](docs/OPERATIONS.md). Do not run an independent resource mutation/probe while the app is drawing. Resource-absence evidence belongs at completed stopped handoffs, not while an active worker legitimately owns bitmaps.

### 5. Commit and leave running

```sh
python3 tools/persistent_install.py commit --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD" \
  --startup-confirmed --navigation-return-confirmed \
  --radio-return-confirmed --cleanup-confirmed
```

The confirmation flags represent actual observations. The command checks the trial boot boundary, consumed token, both startup after-images, both mapped hooks, every installed file hash, advancing heartbeat, a healthy running worker, at least three worker starts/two clean stops, committed active/idle transitions for both lanes, at least five minutes of resident uptime and at least 1200 frames in the final active journal. Independently verify the actual uninterrupted duration; the code's frame-count check is not a separate five-minute worker stopwatch.

Commit writes persistent `enabled` and keeps the current run alive. Perform the final normal restart, confirm automatic return, save evidence, and leave the accepted app enabled. A full cold vehicle sleep/wake test is distinct; report it as untested until performed. Do not restore factory startup merely because a successful test session ended.

## Disable and restore factory startup

Keep the original kit and `installer.json`; they are needed for exact rollback. Do not delete release files, kill the worker, or replace configuration files by hand as a normal uninstall procedure.

```sh
# Cooperative verified stop, then disable future activation.
python3 tools/persistent_install.py disable --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD"

# Restore exact original configuration bytes and read-only protection.
python3 tools/persistent_install.py rollback --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD"
```

`disable` requires a reachable resident returning CLEAN. If the resident has already exited/quarantined, do not assume that command can succeed; inspect state and follow the rollback/recovery path. Rollback requests CLEAN when the broker socket exists, writes disable state if needed, and restores only the known after-images (or accepts already-restored originals). An unexpected configuration stops restoration. A stale socket or failed cleanup can also stop rollback; retain evidence and use the previously verified normal restart recovery before trying again.

Restoring files does not unload already-mapped hooks. After rollback, perform a normal restart and confirm factory navigation, radio, HUD and iDrive are normal, then run:

```sh
python3 tools/persistent_install.py verify-restored --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --head "$HEAD" \
  --factory-normal
```

This verifies a new boot, exact originals, absent hooks and absent runtime directory. Rollback intentionally leaves inert release/backups/gate files; it is restoration of factory startup, not a full file purge. There is no general in-place upgrade or re-enable command. Service an existing installation using its evidence and a reviewed change plan, not by rerunning fresh preflight/staging.


## Current baseline package and component rollback

Use `installed/manifest.json` from **Supra-HUD-V1-Current-Baseline-2026-11-18.zip** for final component/configuration comparisons. `rollback/prior-installed-package/` preserves the complete immediately preceding package. That version still checked all factory bitmap slots and could suppress the tach; it is a known fallback, not a newly accepted baseline. The original Gold tag/package remains separately preserved.

For a component rollback: capture permanent/RAM evidence; cooperatively stop and verify cleanup; prevent automatic activation during replacement; compare exact currently installed bytes; stage and read back the selected archived component; restore protection; deliberately re-enable only after resource/identity checks; restart normally and verify. Keep fault records and archive activation tokens rather than restoring old tokens blindly. Do not treat this description as a universal automated upgrade command.

Full factory restoration uses the original startup configurations and the installer state from the original installation. The private archive includes that state when available plus the current configuration before/after images. Retain its pinned kit; do not fabricate installer state or substitute a different manifest to satisfy assertions. The public runtime ZIP alone is insufficient for full installation or rollback on another car.
