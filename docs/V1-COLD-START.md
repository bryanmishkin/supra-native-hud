# V1 cold-start failure: repair candidate and single-session plan

17 November 2026. Owner reports no tachometer after a cold vehicle start. The earlier unplugged iDrive reset passed; it was a warm restart, not proof of cold-wake reliability. The first-failure capture and reviewed recovery are recorded below. V1 Gold Master and V2 remain unchanged; this branch is a V1 repair candidate, installed for validation but not yet accepted for cold sleep/wake.

## Live first-failure finding

The untouched first capture on 17 November reports **`factory transport closed`**, not the hypothesized RPM exhaustion. All 13 payload hashes and both startup configurations match Gold; enabled persistence remains present. No resident or worker is running and RAM runtime state is absent. Read-only correlated presence queries confirm all ten bitmap slots empty. The permanent disable is the confirmed startup blocker; the exact timing of the earlier connection closure is not preserved.

The live candidate additionally makes `factory transport closed` boot-local **only when the worker has exited with proven cleanup**, or no worker ever started. It does not ignore TCP closure or resume drawing in the faulted boot. A closure with failed removal remains persistently disabled; both paths have native regression coverage. Same-boot wake remains a separate validation point.

The recovery tool's explicit `--factory-close-recovery` option accepts only that exact legacy reason, matching Gold files and stopped processes. It verifies the entire bitmap pool empty twice, including immediately before archiving the reason. This is a reviewed one-time recovery, not automatic deletion of arbitrary faults.

The first live patch transaction found that this target has no shell `sync` utility. Its rollback restored all three originals and retained disable. The corrected package uses the native resident's `--sync-state` operation; each archived fault gets a unique backup name. No application was started by that failed transaction.

## Reproduced defect and bounded fix

On Gold Master, four consecutive unstable RPM transport failures with verified clean removal exhaust the retry budget and write persistent `disabled` containing `clean I/O retry budget exhausted`. That token prevents subsequent boots even though no custom resources remain. Engine telemetry loss during shutdown is one possible trigger, not a confirmed diagnosis of this car.

The regression reproduces that permanent disable on the old source. The candidate keeps the same retry budget and stops for the remainder of that head-unit boot, but does not create a persistent disable for this exact reason when the worker has exited and cleanup is proven. A fresh boot still starts both factory lanes Unknown and cannot draw until both have acknowledged idle commits. The exact clean factory-closure case described above is also boot-local; other faults retain permanent quarantine. Existing operator/fault disable files are never automatically erased.

This does not implement same-boot recovery after exhausted retries, nor does it establish how this car's sleep/wake preserves head-unit RAM. A wake without a new head-unit boot may still require a separate fix. Collect evidence rather than claiming a warm reset solves cold wake.

Three changed target executables: resident, navigation gate, HMI gate. Worker, renderer, profile, navigation hook and startup configuration bytes remain the accepted V1 versions. Gates retain bounded last-decision records; resident retains the last terminal reason and captures startup errors. Per-second RAM admission state reports Unknown=0, Idle=1, Active=2 and pending requests. These records explain failed startup without more blind restarts.

## Offline evidence

- Old resident fails the new next-boot assertion: `clean RPM exhaustion persisted across boots`.
- Corrected native integration passes next-boot re-admission, navigation/radio cleanup and return, pre-admission takeover, and uncertain-ACK quarantine.
- Python tests cover gate fallback, narrow repair eligibility, default no-network behavior, successful patch transaction, and rollback after a partial upload. A fake filesystem transaction is not target execution.
- QNX ARM build and static dependency/import audits pass for all three replacement executables. These are not cold-start acceptance.

Private evidence bundle contains exact build hashes, audits, test logs, patch kit, original Gold kit, original installer state, and source snapshot. No proprietary binary/profile is committed to GitHub.

## First car checkpoint: preserve the failure

Park outdoors with engine running and normal factory HUD visible; guidance stopped, radio closed. Connect ENET. **Do not restart iDrive or clear a token before the first snapshot.** Establish the existing verified SSH master; these tools never unlock SSH or guess credentials.

From the source checkout, with paths set to the private package and a new evidence directory:

```sh
python3 tools/capture_cold_start.py --execute \
  --v1-kit "$PATCH_KIT/gold-master" --ssh-socket "$SOCKET" \
  --output "$SESSION/01-before"
```

Capture reads the disable reason first, then tokens, RAM status/journals, interfaces/routes, process identities/maps, startup capture and exact installed hashes. It samples live state twice. Missing files and command failures are retained. Inspect `capture.json`, original stdout/stderr and advancing journal; status alone is not visual proof.

If SSH is unavailable, preserve that fact. Do not change startup or claim a diagnosis without accessing its saved state. If initial state differs from the reproduced failure, inspect this comprehensive snapshot while still connected. Do not apply the narrow repair to an unrelated fault.

## Repair only when exact condition matches

```sh
python3 tools/repair_clean_rpm_disable.py --execute \
  --kit "$PATCH_KIT" --capture "$SESSION/01-before" \
  --ssh-socket "$SOCKET" --output "$SESSION/02-repair"
```

The repair requires the exact Gold manifest, all 13 installed payload hashes plus both startup files, the exact clean-RPM disable reason, enabled persistence, no resident/worker and no broker/handoff sockets. It rechecks the live state. Unexpected bytes or state stop the repair.

Only the resident and two gates are replaced with same-directory staging and byte-for-byte readback. Read-only filesystem protection is restored and checked before archiving the exact legacy disable token as a unique `disabled.before-cold-start-fix-*` file. Enabled state and startup configs are preserved. No reboot or drawing process is started by the tool. On a transaction failure it attempts restoration of the original three binaries and retains disable; retain the log if connection loss prevents verifying rollback. It is intentionally not a generic upgrader or arbitrary fault reset.

## Acceptance in the same session

1. Owner performs the already-verified normal iDrive restart. Allow at least the resident's 30-second settle period and require observed idle commits. Confirm smooth plausible live RPM with no symbols; capture a new snapshot.
2. Start navigation: tach disappears, factory guidance normal in both displays, cleanup proven. Stop guidance: tach returns automatically. Repeat radio open/close twice. Capture handoff journals and resident status.
3. Save all evidence **before** shutting the vehicle down. Observe the natural engine-off behavior; do not generate display commands during shutdown. Record exact shutdown, lock, wake and start times. Disconnect any connection that keeps the head unit awake. Do not substitute a volume-button reset for actual sleep/wake.
4. After actual vehicle sleep/wake, start normally and check automatic tachometer with the Mac disconnected. Reconnect for a fresh snapshot. Compare process/runtime evidence to distinguish a fresh head-unit boot from retained RAM. If sleep cannot be established in the available time, label cold-sleep acceptance incomplete; no guessed fixed wait proves sleep.
5. Repeat navigation/radio return and save final live health, read-only filesystem state and visual observations. Leave running only if accepted. Retain the Gold original kit and installer state for the existing documented factory-startup rollback.

Post-patch snapshots use `--v1-kit "$PATCH_KIT/patched-reference"` for current installed hashes; the tool's historical JSON field is still named `gold_master_comparison`. This combined reference is for verification, not a new accepted release or fresh installation package.

A real cold-start success is the missing acceptance criterion. The offline tests prove the code defect and its correction; they cannot prove which failure the vehicle experienced or guarantee recovery from all sleep/wake paths.

The corrected second transaction completed: replacement bytes read back exactly, empty resource pool verified twice, filesystem protection restored, original reason archived, enabled token retained, native sync completed. No automatic restart was issued. Owner restart and cold-wake validation are pending.
