Latest prepared test: [explicit empty guiding model and cooperative navigation yield](SMOOTH-NAV-NEXT-TEST.md). The smooth live-RPM control is preserved.

Latest result: [smooth 30-second live RPM drawing verified](LIVE-RPM-SMOOTH-RESULT.md), with complete cleanup and normal factory-function checks. Circle removal and automatic coexistence remain unresolved.

Latest offline update: native tachometer frames and the bounded next drawing test are prepared. See [TACHOMETER-NEXT-TEST.md](TACHOMETER-NEXT-TEST.md) for validated scope, factory-navigation handoff and exact pass criteria.

> On-car update, 16 Nov 2026: the loader, ten self-tests, replay and registry/overlay observations now pass. The expected 0x82/0 HUD service was absent in every window. See CAR-VALIDATION.md for measured results and cleanup. Earlier planned checks below are retained as procedure/history, not outstanding execution tasks. Live drawing remains blocked on actual Supra transport discovery.

# HUD application status — 16 November 2026

## Implemented and tested offline

The C++98 core draws a normalized 24-segment upper tach arc and five progressive shift indicators. Defaults suppress output; RPM thresholds, object ownership and overlay state must be explicitly validated. Optional pressure calculation uses fresh paired manifold/ambient samples; the native renderer does not yet render numeric boost text.

The core rejects invalid/future/stale RPM, out-of-order source timestamps and clock rollback even between presentation frames. Source timestamps are preserved; cached readings must not be restamped. Input safety can now be checked on an acknowledgement without consuming the next presentation slot.

The native encoder creates bounded commands only for two explicitly owned handles. It builds a hidden back buffer and switches visibility last. The session permits one outstanding command, requires an exact correlated acknowledgement, and stops on timeout, send failure, permission loss or clock rollback. A queued frame expires using its original sample timestamp; fresh incoming samples do not extend it.

The application controller coordinates those components without opening a connection. The observer creates temporary DSI registration/subscriptions and captures at most eight registry snapshots and 256 HUD headers, without payloads. It sends no HUD commands. Its 15-second observation has a 20-second hard deadline.

Three QNX ARM candidates compile: registry observer, offline replay and no-vehicle-I/O self-test. The self-test covers ten cases and has a five-second deadline. Linux tests run on both 32-bit and 64-bit hosts; target compilation is distinct from target execution.

## Important limits

The encoder emits 40 calls per full frame. At the current 50 ms minimum spacing, the sequence needs at least 1.95 seconds. Production input freshness is 300 ms, so the frame-expiry guard intentionally prevents that slow sequence from becoming a live tachometer. The simulator uses a declared 2000 ms synthetic fixture budget to exercise completion; that is not approved for live use.

Stopping local sends does not remove a previously visible remote image. The native service's lifetime/release behavior must be verified before live drawing. Unknown overlay state, ownership or echoed-tag behavior cannot be solved with a guessed profile.

## Remaining work that needs car evidence

- Execute the self-test and confirm the target loader/C++ runtime.
- Validate the private DSI adapter through bounded registry observation.
- Determine the actual HUD host, ownership/acquisition/release, geometry and palette.
- Validate reply correlation and a transport/update strategy fast enough for fresh RPM.
- Establish factory overlay signals and verified cleanup/recovery behavior.
- Bind a validated live telemetry source and agree the car-specific shift thresholds.
- Implement the live sender/profile only after those facts are established.

No persistent startup, global HUD clear, firmware change or coding operation is implemented. See NEXT-CAR-SESSION.md for the ordered tests.
