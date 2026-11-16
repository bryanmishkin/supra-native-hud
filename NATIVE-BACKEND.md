> On-car update, 16 Nov 2026: the loader, ten self-tests, replay and registry/overlay observations now pass. The expected 0x82/0 HUD service was absent in every window. See CAR-VALIDATION.md for measured results and cleanup. Earlier planned checks below are retained as procedure/history, not outstanding execution tasks. Live drawing remains blocked on actual Supra transport discovery.

# Native drawing backend candidate

The new C++98 adapter `src/native_backend.*` encodes the HUD core into native MOST HUDTerminal calls using the published related project's `hudterm.hpp` payload builders. It is a command encoder with acknowledgement-controlled buffer selection, not yet a connected drawing application. It has no socket or device-control registration and cannot send a command to the car by itself.

A valid explicit profile must confirm MOST HUDTerminal transport, dimensions, palette and owned image instances. There is no default Supra profile. The test's host 0x0101, handles 20/21 and 480x240 dimensions are synthetic fixtures, not discovered or authorized car settings. The J29 SOME/IP navigation-graph alternative is not implemented as an arbitrary drawing transport.

Each frame prepares a hidden owned back image, removes only its items, adds 24 tach segments and five shift indicators, then emits a final visibility swap. This is 29 items in 40 commands. Colour values are palette indices supplied by the verified profile, not assumed RGB values. Coordinates are bounded to the verified image dimensions. Invalid geometry/nonfinite coordinates, duplicate handles, insufficient item capacity and unconfirmed profiles produce no commands.

Buffer roles advance only after the caller confirms every command succeeded. Failed acknowledgement latches failure. Only one batch may be pending. Disconnect, unknown overlay state or factory overlay activity invalidate the session and require fresh verification. ClearOwned emits only two hide commands for the profile's two owned handles. There are no global reset, instance-creation, release or factory-frame commands.

## Integration contract and remaining work

- Allocate/acquire genuinely owned image objects and establish parent placement through a verified native lifecycle before supplying a profile. Hardcoding free-looking factory handles is not ownership.
- The future live sender must recheck permissions before every send, cancel queued commands on revocation, correlate every acknowledgement, enforce a finite timeout, and invoke complete(false) on partial/error/timeout outcomes. Never call complete(true) merely because writes succeeded.
- A late acknowledgement after invalidation must not restore readiness. A new session must reacquire ownership and determine current visibility. Ambiguous partial swaps require recovery, not blind retry.
- A 40-command frame at a 10 Hz core ceiling would imply up to 400 method calls/sec. This is NOT a validated budget and must not be used as a production rate. Measure bandwidth, acknowledgement latency and factory coexistence first; add bounded coalescing/change-only updates or lower cadence before live rendering. Hidden back-buffer construction prevents intended partial presentation but does not make the bus load safe.
- The upstream 6WA transport defaults to 32 calls/batch. This candidate's 40 calls exceed that limit; it is intentionally not wired directly into that transport. Do not raise the limit blindly. A verified sender must stage batches or reduce commands while preserving the final swap ordering.
- Numerical RPM/boost text and their owned text objects are not implemented in this backend. The current encoder draws the tach and shift cues only.

Tests run in 32-bit and 64-bit Linux and cover command shapes, big-endian swap bytes, pixel bounds, 29-item capacity, allowed handles, clearing only owned images, acknowledgement-driven alternation, failure latching, overlay invalidation and invalid input/profile rejection. No live compatibility claim follows from these tests.

Follow-up: added and tested ordered staging of the 40-command plan into batches of 32 and 8. The final visibility swap remains in the last stage. This resolves the encoding-size mismatch; a live sender must still wait for every prior-stage acknowledgement and recheck permissions before advancing. It does not resolve throughput or runtime compatibility.

## Post-capture offline update

See OFFLINE-READINESS.md for the current consolidated status. Strong symbol-name closure and 59 versioned imports now resolve against the actual captures; App/Core/DSI repeat captures match. Native session sequencing and timeout/cancellation logic is implemented and host-tested, but no live transport binding exists and its strict echoed-tag acknowledgement contract remains unverified on the Supra. The myQNX account was signed in but still processing.

## Frame-age enforcement update

Frames carry the source sample timestamp and permitted age. The native session checks the queued frame's own expiry on sends and replies, even when newer telemetry arrives. Production TTL remains 300 ms; the slow 40-call/50 ms diagnostic sequence cannot finish inside it. Replay uses an explicit 2000 ms synthetic fixture only. No live sender is enabled.
