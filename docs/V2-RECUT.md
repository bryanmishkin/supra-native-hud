# V2 recut — 18 November 2026

V2 includes the complete `v1-baseline-2026-11-18` source ancestry. The installed V1 remains unchanged. The native worker keeps V1 factory RPM, movement/background authorization and checks only owned bitmap slots 8/9. Resident recovery, permanent fault logging, hook and startup sources are unchanged from that baseline.

Candidate worker SHA-256: `6b8653c2728be49aae49c25853ba951890fdd80d32184cdb96499734e6a338a5`. Private kit: `v2-recut-2026-11-18/car-kit`. This kit pins the exact V1 manifest `ac903624ebda36039885a2d2fb36cc3f5d9403f22b554d448ab8ae584268c6c7`; older V2 kits must not be used.

## Offline evidence

- QNX ARM build and captured-library static audit passed.
- 258 Python tests passed using the existing analysis environment.
- Renderer/pressure unit checks, eight V2 loopback cases and twelve worker regressions passed.
- Dedicated V2 factory-feed checks cover normal drawing without diagnostic gateway requests, stale-feed cleanup and unavailable-feed refusal.
- Dedicated V2 resource checks cover coexistence with factory slots 0..7, refusal of occupied tach slot 8 or 9, and preservation of factory images.
- V1 resident, hook, native RPM implementation and startup code match the baseline source; V2 selection remains explicit. Classic/sport renderer paths are retained.

These are offline tests, not projected readability or target timing acceptance. The optional pressure reader is an additional feature, remains uncalibrated and is excluded from visual-only testing.

## Focused car test

Use [V2-CAR-TEST.md](V2-CAR-TEST.md), beginning with healthy V1. Preflight checks the exact installed baseline, stages V2 only in RAM and tests its loader. Cooperatively pause V1, run the 30-second layout mode, confirm readability/colors/smooth RPM and clean removal, then collect results. PSI remains unavailable (`--.-`) in this mode. Do not run V1 and V2 simultaneously.

A short takeover check is available to confirm this candidate's cleanup. A normal iDrive restart returns the untouched V1 installation; verify original hashes and advancing RPM before unplugging. This is a smaller validation scope than reinstalling/retesting V1 startup. It does not install persistent V2 or imply its automatic return has been car-tested.

If the layout is accepted, a persistent V2 selection is a separate next step. No boost polling or permanent upgrade is enabled implicitly by this trial.

## Subsequent vehicle test

[The layout test passed visually and exact V1 restoration was verified](V2-LAYOUT-RESULT.md). An extended layout-only worker was built during the session; use that result for its hash and duration limits. V2 remains a temporary test, not a persistent installation.
