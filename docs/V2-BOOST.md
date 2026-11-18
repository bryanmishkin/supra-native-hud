# V2 boost integration — 18 November 2026

The V2 worker connects paired pressure readings to the signed PSI field in explicit `--parked-v2-boost-candidate` mode. Layout-only mode still makes no pressure requests. This is a compiled, offline-tested candidate, not a deployed or calibrated boost gauge. V1 and its archived baseline remain unchanged.

## Behavior

- Reads DME 0x12 DIDs 0x4205 and 0x4201 through the internal diagnostic gateway, using a shared 100 ms deadline per pair.
- Candidate absolute kPa = big-endian raw / 128; ambient kPa = raw / 256; gauge PSI = (absolute − ambient) × 0.1450377377.
- Uses factory EngineSpeed2 for RPM independently of diagnostic pressure polling.
- Only a complete, correctly addressed, plausible, fresh pair can show PSI. Missing/stale/invalid pressure shows dashes; no cached value receives a new timestamp.
- Three consecutive failures trigger a one-second cooldown. Continued failures remain rate-limited; success resets the count and normal polling resumes. RPM and cleanup remain active during cooldown.
- Boost stays explicitly opt-in and bounded to 30 seconds. Layout-only supports up to 120 seconds. The separate pressure-only probe still requires all 40 pairs to pass before the runner allows combined drawing.

## Build and offline evidence

Worker SHA-256: `d4221ed7ed3faa87dca55799545b9028f91de96351e9b6638d0951623912b565`.

Private prepared package: `v2-boost-2026-11-18/car-kit`; exact V1 fallback manifest: `ac903624ebda36039885a2d2fb36cc3f5d9403f22b554d448ab8ae584268c6c7`.

QNX ARM build and captured-library audit passed. 259 Python tests passed. Integration evidence includes 12 legacy-RPM loopback cases, 12 factory-RPM cases, two additional factory-RPM dropout/partial-pair cases, and 12 existing worker regressions. Unit tests also cover stale/future/skewed samples and malformed/sentinel replies.

Cases cover near-ambient replay, synthetic positive pressure (+14.50 PSI), synthetic vacuum (−7.25 PSI), delayed replies, incorrect identifiers, unavailable input, complete timeout, cooldown recovery, valid-to-invalid-to-valid transition, partial-pair failure and cooperative cleanup. These synthetic values test arithmetic and rendering, not actual engine pressure accuracy. Factory-feed cases made zero diagnostic RPM requests. Layout-only made zero pressure requests. Factory bitmap resources were cleaned up in all successful integration outcomes.

Logged native-simulation RPM sample gaps reached 400 ms in the partial-pair timeout case; the main factory-feed suite reached 300 ms. Host scheduling and simulated feed timing do not establish actual head-unit cadence. Measure it in the target test rather than promise unchanged timing.

## Signal evidence and limits

The original reference signal table describes Gen 1 B58/340i candidates. Our saved Supra replies (`62 42 05 31 ec`, `62 42 01 63 d3`) correspond to roughly 99.84/99.82 kPa, consistent with a near-ambient point only. They do not establish sensor location, vacuum response, positive-boost scaling or calibration on this Supra.

The pressure route is still diagnostic-gateway based. Unlike the proven factory RPM feed, its availability without a connected laptop/ENET has not been established. Do not advertise standalone live boost until that is checked. No car access occurred during this offline work.

## Next car test

Use [the staged V2 runbook](V2-CAR-TEST.md) with this new kit, preserving V1. Start with read-only pressure acquisition while parked. Save raw replies, timing and engine state. If its gate passes, run the explicit 30-second combined candidate and check PSI/dashes, RPM smoothness and cleanup. Capture before restarting and verify the unchanged V1 afterward.

A later signal comparison must establish pressure accuracy against an independent trusted measurement under appropriate conditions, plus cable-free availability. Stationary revving alone is not positive-boost calibration. Persistent V2/boost deployment is separate from this bounded test.
