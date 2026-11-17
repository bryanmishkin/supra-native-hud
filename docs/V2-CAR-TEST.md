# V2 layout and candidate boost: prepared car test

This is a **bounded test**, not a V2 persistent upgrade. The original V1 Gold Master tag and archive stay intact. The accepted startup-repair kit, installed binaries, startup configuration and enable/disable tokens remain unchanged. V2 runs from a unique `/tmp/supra-v2-*` directory; the installed V1 resident is stopped cooperatively for the test. A normal owner-operated iDrive restart resumes the unchanged V1 installation.

Do not run the new worker beside the active V1 tachometer: both use the same reviewed shared guidance resources. Do not disable V1 persistently, overwrite its executable, delete a quarantine token, or claim that V2 is installed after this procedure.

## Accepted runtime carried forward

Merged accepted source `377d3fe`: 500 ms correlated drawing ACK allowance, clean input recovery with bounded retries, boot-local clean connection closure, retained gate diagnostics and native state sync. RPM freshness stays 300 ms and uncertain drawing cleanup still quarantines. Both the V2 pressure probe and worker use internal source `160.48.199.119` and gateway `160.48.199.16`; SSH remains at `169.254.199.119`. The persistent resident still selects V1 sport; V2 display and candidate boost remain explicit bounded modes. No connection to the car or persistent change occurs during preparation.

The runner pins accepted baseline manifest SHA-256 `605bd081a435866006a9267ac1bacc8a41d9fd1593c87984ac9d361ece5933c1`, checks every installed payload and startup file, and rejects the old Gold kit. It never downgrades the repaired V1 to Gold.

## Prepared implementation

- Native QNX ARM worker with explicit `--parked-v2-guidance-stopped` and `--parked-v2-boost-candidate` modes; both limited to 1–30 seconds. The car runner uses 30 seconds.
- Layout-only mode reads RPM and shows `--.-` PSI. It makes no pressure requests.
- Experimental boost mode reads the two already-observed DME candidates, then a fresh RPM sample. Pair acquisition has a shared 100 ms deadline; RPM retains its 200 ms transport deadline and 300 ms freshness budget.
- Missing/invalid pressure makes the PSI field unavailable. Three consecutive pair failures stop pressure polling for the remainder of that bounded run; RPM continues if healthy.
- The existing core checks paired pressure freshness (300 ms), timestamp order and maximum 100 ms pair skew before rendering. No cached pressure is restamped. Logs preserve bounded raw pressure replies, request/receive timestamps, converted pairs, and whether each frame actually displayed boost. Pressure acquisition is included in the 250 ms cycle target, rather than adding a fixed delay to every RPM cycle. Actual target cadence is still a car-test measurement.
- Drawing dimensions, bitmap IDs, symbol-free profile, double buffering and cleanup are unchanged. The V1 hook's existing direct-worker fallback handles pre-send cleanup while the V1 resident broker is absent.
- **V2 automatic return is not part of this temporary test.** A factory takeover ends the bounded worker; it does not restart itself. The normal restart restores V1's resident and automatic return.

## What we know about pressure

Saved reference-car replies from 16 November 2026:

| Request to DME 0x12 | Reply | Candidate conversion |
| --- | --- | --- |
| `22 42 05` | `62 42 05 31 ec` | big-endian raw / 128 = 99.843750 kPa absolute candidate |
| `22 42 01` | `62 42 01 63 d3` | big-endian raw / 256 = 99.824219 kPa ambient candidate |

Candidate gauge PSI is `(absolute_kPa - ambient_kPa) * 0.1450377377`, about +0.00283 PSI for those observations. Conversion provenance is the previously inspected reference project's signal definitions; these two replies corroborate only a near-ambient point. **Exact sensor location/meaning and positive boost accuracy under load remain unverified.** These are not described as certified manifold pressure or a calibrated boost gauge.

The new reader accepts only exact five-byte positive responses with the requested identifier. It rejects truncated/extra/wrong-ID responses, zero/all-ones raw candidates, absolute values outside (0,400] kPa and ambient values outside [50,120] kPa. Bounds are diagnostic plausibility checks, not proof of semantics. No diagnostic-session change, engine command or DTC clearing is sent.

## Offline preparation

Build using the existing QNX environment. The old compiler requires global `::snprintf`, now used by V2. Audit the worker against captured target runtime libraries, then prepare:

```sh
python3 tools/prepare_v2_test.py \
  --binary build/supra-standalone-parked-qnx \
  --audit /private/v2/v2-arm-audit.json \
  --v1-kit /private/v1/watchdog-fix/patched-reference \
  --output /private/v2/car-kit
```

The output must be new. This tool pins the exact accepted startup-repair reference kit and refuses a stale/failed ARM audit. It packages the exact V2 binary/profile and an unchanged copy of the V1 kit. It has no network or installation behavior. This is specifically for the reference vehicle with V1 already installed, not a new-vehicle installer.

Offline reproducibility (host compiler, libpcap headers/library, Python):

```sh
sh environment/test-v2-offline.sh /private/v1/supra-profile.bin /tmp/v2-offline-check
```

This exercises candidate pressure decoding, the renderer, eight V2 loopback cases (including a delayed drawing ACK) including cleanup, plus the existing twelve worker regression cases. Static audits and loopback tests do not establish actual QNX execution latency or projected color/readability.

## One coordinated parked session

Park outdoors, engine running, HUD visible. Begin with healthy V1 and normal factory functions. Do not combine this with tonight's V1 road test or begin driving while the RAM candidate is running. Keep the normal restart/recovery method available.

```sh
KIT=/private/v2/car-kit
EVIDENCE=/private/v2/car-session
SOCKET=/private/verified-ssh-master

# No connection: inspect the phase plan.
python3 tools/run_v2_validation.py preflight

# Verify running V1, all installed hashes/configs, hooks, enable state and RO mount.
# Stage only the RAM candidate and profile; run the no-vehicle-I/O loader self-check.
python3 tools/run_v2_validation.py preflight --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET"
```

`EVIDENCE` must be new. Use the same kit/evidence for every phase. All phases default to no network without `--execute`. Use normal Python, not `python -O`, because validation includes assertions.

1. Stop guidance, close the radio selector, confirm normal displays. Then pause V1:

```sh
python3 tools/run_v2_validation.py pause-v1 --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --guidance-stopped
```

The tool requires CLEAN, final STOPPED resident status and absence of its broker/worker sockets. It saves the V1 checkpoint. Confirm visually that the V1 tach is gone before proceeding. No enabled/disabled token changes occur.

2. Run layout-only for 30 seconds. Confirm bigger bar/lights, smaller digits, no clipping/flicker/symbols, correct plausible RPM, and PSI dashes. Keep factory overlays closed throughout.

```sh
python3 tools/run_v2_validation.py draw --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" \
  --guidance-stopped --visual-cleanup-confirmed
```

After completion, verify graph/bitmap cleanup in the result and visually verify both displays are normal. A prior active journal is archived in the RAM trial directory before another run; the shared handoff socket path is reused only after confirming no worker owns it.

3. Read pressure only, without HUD drawing, for 40 pairs (about 10 seconds):

```sh
python3 tools/run_v2_validation.py probe-boost --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" \
  --guidance-stopped --visual-cleanup-confirmed
```

Inspect pair success, values, timing and plausibility against the current engine state. This is a transport/readout gate, not positive-boost calibration. If incomplete, retain evidence and continue layout work without enabling the boost display.

4. If all 40 pairs passed and the owner agrees to viewing an explicitly experimental pressure-derived readout, run the combined 30-second candidate:

```sh
python3 tools/run_v2_validation.py draw-boost --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" \
  --guidance-stopped --visual-cleanup-confirmed --candidate-boost-confirmed
```

Check smooth RPM, optional PSI value/dashes and clean timed removal. Do not rev to prove positive boost; an independently referenced signal comparison under appropriate conditions is a later telemetry-validation task.

5. Test factory takeover after displays are normal again. The `yield` phase runs the layout-only worker for up to 30 seconds. Wait until recording/display is running, then open **one** factory function (guidance or radio). Require the tach to disappear, factory display normality and `factory_navigation_request` with verified cleanup. Repeat for the other function with a new current normal-display confirmation. The same reason name is used for radio handoff.

```sh
python3 tools/run_v2_validation.py yield --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" \
  --guidance-stopped --visual-cleanup-confirmed
```

If no factory takeover occurs in that window, the tool does not count a timed end as a successful handoff. If cleanup is uncertain or execution is interrupted, it records recovery required and refuses further drawing. Preserve evidence and use the normal restart recovery.

6. Collect before restarting. Then perform a normal owner-operated iDrive restart, re-establish the authorized diagnostic connection, and confirm the original V1 tachometer has returned. This clears RAM trial files; no persistent undo is required.

```sh
python3 tools/run_v2_validation.py collect --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET"

# AFTER the owner's normal restart and visual confirmation:
python3 tools/run_v2_validation.py verify-v1 --execute \
  --kit "$KIT" --output "$EVIDENCE" --ssh-socket "$SOCKET" --v1-visible
```

Final verification requires the temporary trial directory gone, original V1 installed hashes/configurations unchanged, enabled state intact, hooks present, healthy running V1 worker, advancing heartbeat, and advancing RPM frame/sample timestamps (a heartbeat alone does not prove a live gauge). Briefly check navigation/radio return and factory normality before unplugging. Save user observations separately from machine results. If verification fails, investigate the actual state rather than claim restoration.

## Evidence to keep

The local `v2-session.json`, numbered stdout/stderr, pre/pause/post V1 checkpoints, per-run journals/results, pressure probe pairs, source/binary/profile hashes and exact visual observations. Keep these separate from Gold Master and road-test records. The private prepared kit and target audits belong in Drive, not GitHub.

## 17 November offline integration check

Accepted repair source `377d3fe` is merged. QNX ARM worker SHA-256: `aaefadfcf29a8f0c5fa4fb6eb2baa2ac8ea777c435a0b722218f40c1d834d2e0`. Captured-library static audit passed; 256 Python tests, eight V2 loopback cases, twelve worker regression cases, and the resident recovery/race/cleanup suite passed. Twelve classic/sport frames match accepted V1 source byte-for-byte. Five V2 preview frames round-trip through the corrected wire codec.

**Deployment hold:** owner subsequently reported another cable-free startup with no initial tachometer; it later appeared after ENET connection, without resetting iDrive. Saved packets show eight internal gateway connection rejections before successful RPM replies. Startup delay versus cable activation is under investigation. These offline tests do not resolve that vehicle dependency. No V2 deployment occurred.

The reproduced false startup-watchdog lockout is also merged from `0d33b5e`; the baseline pin now follows the exact installed watchdog-repair kit. A fully cable-free ten-minute shutdown/start check is in progress. V2 remains a separate temporary test candidate.
