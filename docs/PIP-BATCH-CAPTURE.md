# One-session PiP investigation batch

Prepared offline, 18 November 2026. This is an investigation batch, not a larger-area drawing test. Keep the installed V1 worker/startup unchanged. No restart, SSH activation, drawing requests, session creation, bitmap removal or screen/window mutation is part of this plan.

## Questions to answer together

1. Is the native PiP window identified by caption/class/ID string `1056` actually present during factory navigation on this Supra?
2. Which navigation displayable is active: command-only, native window, or bitmap export? Correlate display/session identifiers with process and shared-memory inventories; file presence alone is insufficient.
3. Do B006 picture-in-picture resources or B009 sink changes coincide with navigation transitions? Is radio still exclusively B00E in the new window?
4. Is there an observable pixel-output destination for that native window? A native window's existence does not prove windshield routing.

## Batch sequence

Use one uninterrupted **120-second** capture from the existing hash-verified `hud_continuous_capture` through `consolidated_capture.py --record-only`. Confirm `recording_ready` before owner actions. Do not start the recorder late after navigation has already changed. Run the phase metadata collector alongside it from a separate local process.

| Phase | Owner action while parked | Collect |
| --- | --- | --- |
| normal | Guidance stopped, radio closed | Phase metadata; begin packet capture |
| radio-open | Open selector, keep visible briefly | Phase metadata; timestamp visible confirmation |
| radio-closed | Let selector close | Phase metadata; timestamp closure |
| navigation-start | Start guidance after recording-ready instruction | Phase metadata and transition marker |
| navigation-visible | Confirm instruction visible, leave active | Phase metadata; inspect window/buffer inventory immediately |
| navigation-stop | Stop guidance | Phase metadata and transition marker |
| normal-final | Confirm normal factory display | Phase metadata and final inventory |

Do not rush actions to fit a timer. If all phases do not fit, repeat only the remaining transition in another 120-second window **during the same visit**, after confirming recorder readiness. Do not require driving or revving.

`collect_pip_phase.py` defaults to a no-network JSON plan. Execution requires explicit verified addresses and known-hosts, e.g.:

```sh
python3 tools/collect_pip_phase.py --execute --phase navigation-visible \
  --head "$HEAD" --local "$LOCAL" --known-hosts "$KNOWN_HOSTS" \
  --output "$PRIVATE_SESSION/phases"
```

Its fixed read-only commands are `uname -a`, `pidin ar`, `netstat -an`, `ls -l /dev/shmem`, and `ls -l /dev/screen`. It timestamps and hashes each result, limits command duration to 20 seconds, rejects oversized saved results, preserves failures, and refuses to overwrite a phase. `/dev/screen` is a discovery inventory, not an assumed available API. Missing inventory is an explicit incomplete result, not permission to probe arbitrary nodes or change graphics settings. Pixel data is not read by this collector.

## Adaptive work while still connected

Review all phase outputs before declaring completion. If a screen inventory exists, first identify its documented/readable metadata interfaces and target the actual window `1056`; do not assume a path or write window properties. If new mapped renderer/provider binaries are identified, retrieve each once with the existing bounded, double-read/hash collector, avoiding already preserved copies. Inspect any relevant `GVBitmap` or `GVCommand` candidates only with known header/length/sequence semantics. Old reusable buffers are not live frames.

The existing shared-memory inspector requires the independent DisplayableData length and sequence for full frame parsing. This batch's metadata snapshots do not themselves supply those events. If a live session/window association cannot be read through available introspection, record that exact gap and the named provider needed; do not claim that packet capture alone answered it. No broad memory dump or unverified hook is prepared here.

## Before unplugging

- Confirm every action has an observed timestamp and a corresponding capture window; repeat missed transitions now.
- Verify recorder exit, packet/drop counters, stream framing, timestamps, local file hashes and remote recorder cleanup using its existing result manifest.
- Review inventories while the session is still accessible. Save unavailable capabilities explicitly.
- Confirm V1/startup files were never altered and factory displays remain normal. This is an observation, not another full navigation acceptance campaign.
- Save the exact evidence bundle privately to Drive. Publish only findings/tools, excluding routes, OEM binaries and captures.

A clean packet capture is not proof of an owned larger surface. The batch is ready for baseline metadata/packet collection; specialized native-window introspection remains dependent on what the actual head unit exposes.
