# Supra native HUD

Personal research project for the **2026 Toyota GR Supra 3.0 Premium, six-speed manual**, with NBT Evo firmware **NBTevo_T24081I**. The intended display is the factory windshield HUD: an upper curved tachometer and progressive shift cues while preserving factory speed, speed limit, navigation and radio overlays.

## Current state

The QNX 6.5 ARMv7 build works. The repository contains the HUD core, native command encoder, acknowledgement sequencer, application controller, bounded registry observer and offline simulators. **There is no enabled live drawing sender, validated Supra drawing profile, or persistent startup installation.**

Production defaults suppress drawing. The active frame's own RPM sample must remain fresh; new input cannot extend an old queued frame. The present conservative 40-call sequence takes at least 1.95 seconds, which exceeds the default 300 ms freshness budget. The replay explicitly uses a 2000 ms synthetic test budget. That is not a production configuration or proven car bandwidth.

## Build and test

Run commands from the repository root.

```sh
# Recreate the ordinary Linux test host (no QNX SDK required).
docker build --platform linux/amd64 -t supra-hud-build-host:22.04 environment
docker run --rm --platform linux/amd64 --network none \
  --mount "type=bind,src=$PWD,dst=/workspace,readonly" \
  supra-hud-build-host:22.04 sh environment/test-host.sh

# On the prepared Mac, using the locally retained SDK image:
sh environment/run-local-sdk-build.sh

# Alternative: supply an independently installed SDK and its configuration.
QNX_SDK_DIR=/path/to/qnx650 QNX_LICENSE_DIR=/path/to/qnx-config \
  sh environment/run-build.sh
```

Neither SDK nor license material is included. The local SDK image is private and is not a GitHub build dependency available to other machines. See [environment/README.md](environment/README.md).

The target build produces:

| Candidate | Purpose | Vehicle-service interaction |
| --- | --- | --- |
| `supra-hud-selftest-qnx --self-test` | Ten bounded synthetic tests plus monotonic-clock use | None; no DSI loading or sockets |
| `supra-hud-offline-replay-qnx --simulate` | Forty synthetic commands emitted as JSON | None; commands remain in memory |
| `supra-registry-observer-qnx --observe-registry` | 15-second registry and bounded HUD-header observation | Temporary DSI client and subscriptions; no drawing/device-control registration |

A successful build is not a target execution result. The upcoming car session must first verify the loader and self-test, then the private DSI adapter. [NEXT-CAR-SESSION.md](NEXT-CAR-SESSION.md) gives the exact order and stop conditions.

## Source map

- `src/hud_core.*`: timestamps, cadence, tach/shift geometry, optional pressure calculation.
- `src/native_backend.*`: owned-handle command encoding and double-buffer batches.
- `src/native_session.*`: one outstanding call, exact acknowledgement matching, timeouts and frame expiry.
- `src/hud_app.*`: single-threaded coordination; no transport connection.
- `src/registry_observer.*`: bounded registry snapshots and header-only observation.
- `tools/hud_selftest.cpp`, `tools/hud_pipeline_replay.cpp`: no-vehicle-I/O target checks.
- `tools/check_session_result.py`: checks saved self-test/observer logs locally.
- `tools/audit_target.py`: static ELF/dependency/import check (requires `pyelftools`).
- `tools/prepare_car_kit.py`: packages hash-matched, audited binaries locally; never uploads or runs them.
- `tools/capture_runtime.py`: default no-network capture plan; explicit read-only execution mode.
- `tests/`: 32/64-bit host tests and Python preparation/result checks.

Runtime captures, SDKs, license utilities/material, credentials, generated binaries and car-session logs are excluded from GitHub. They are not needed to run the host tests. Private evidence and audited candidates are kept separately in Drive. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for vendored source attribution.
