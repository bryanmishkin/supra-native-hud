> Live validation supersedes earlier readiness claims: [results and failed startup integration](docs/v1-native-validation-2026-11-16.md). Native drawing/cleanup passed; controller replacement caused restarts. No unattended installation is accepted. Do not repeat the restart trial.

> Latest startup/rollback and acceptance status (2026-11-16): see [STARTUP-ROLLBACK.md](STARTUP-ROLLBACK.md) and [ONE-CAR-SESSION-V1.md](ONE-CAR-SESSION-V1.md). The executable RAM kit is ready; unattended boot drawing is not accepted.

# Standalone and navigation handoff candidate — 16 November 2026

The proven sport UI now has a direct C++98/QNX runtime candidate. It reads RPM from the gateway, renders and RLE32-encodes the color-corrected 150×36 image, talks directly to the cluster, alternates bitmap slots, and withdraws the same measured symbol-free graph. It requires no Mac, Python or SSH after launch. It has not yet run on the actual head unit; it is not an installed v1 release.

## Components and actual behavior

- `supra-standalone-parked-qnx`: explicit parked/stopped-guidance launch, maximum30seconds, current explicit addresses and monitor interface, new journal, no startup registration. Native 010C reads are bounded to100ms; request age is checked against300ms; update rate is at most4Hz. No writes to engine settings.
- `standalone_wire`: bounded profile reader, SOME/IP correlation and framing, native RLE32 identical to the established Python encoder, display-boundary red/blue swap. Only the known shared profile and two last bitmap slots are used. No instance creation/disposal, blind reconnect or request-ID wrap.
- `navigation_guard`: passive revocation on other traffic to the cluster display endpoint. Validates Ethernet/VLAN/IPv4/TCP bounds and source tuple, ignores only exact observed keepalive payloads, and stops on capture drops/uncertainty. It never infers idle permission from silence. Recorded baseline has0 triggering packets; radio57; watched navigation7; consolidated navigation76. These counts are packet observations, not navigation-event counts or preemption guarantees.
- `libsupra-navigation-handoff-experimental.so`: candidate hook at the captured factory `SomeIP::CSomeIPProtocolAdapter::doSendMessage` entry. For relevant B0xx requests it asks the native app to withdraw through a local Unix socket, waits for `CLEAN`, then calls the original sender. A3-second upper bound and factory priority prevent indefinite blocking if the app fails. `UNCERTAIN`/timeout are explicitly not successful cleanup. With no active app or no configured handoff path, the original sender runs normally.
- Isolated fake-factory self-test: exercises dynamic interposition and the handshake in a separate process; it never attaches to the factory controller. The target package includes this before any proposal to modify factory startup.

## Why both monitors exist

Passive capture observes packets after transmission. Sending the ordinary state5/state0 cleanup after factory guidance has started could cancel the factory display. On passive activity, dropped packets or uncertain transport, the worker stops sending and reports cleanup unverified; it does not delete possibly referenced images or issue global cancellation.

The pre-send hook addresses the normal handoff race: factory transmission is held while the worker finishes any in-flight transaction, withdraws references, disposes tracked images and checks absence. Only then does it reply `CLEAN`. The offline tests caught and fixed a race where an incoming handoff could mark a not-yet-uploaded slot as owned. The cooperative check now occurs between completed transactions.

This is not yet proven in the real factory process. The captured library exports the entry and all three accessor symbols. At0x52cec the508-byte adapter calls the socket sender at0x52e18 and returns its integer result. The captured controller imports that entry. Actual QNX loader interposition, all factory call paths, threading/reentrancy, timing and destination-null behavior still require controlled validation. Host stubs do not prove the real C++ ABI or process integration.

## Offline validation

- Native loopback integration: normal duration, termination signal, occupied bitmap pool, foreign factory traffic, lost reply, wrong reply ID, RPM timeout, monitor loss and cooperative navigation yield.
- Clean duration/signal/RPM-timeout paths withdraw and verify removal. Occupied pool refuses before upload. Factory/monitor/transport uncertainty stops further writes and reports incomplete cleanup. Cooperative yield returns `CLEAN` only after removal.
- Hook tests: clean handshake, null per-message destination, uncertain result, bounded timeout, absent app, non-HUD service, keepalive and unrelated destination. Simulated factory sends remain blocked before the clean acknowledgement.
- Native RLE matches Python byte-for-byte on five real sport frames plus randomized opaque pixels. Packet-parser tests include truncation, fragmentation, VLAN, same-port/different-host traffic and keepalive mutation, with host memory/undefined-behavior sanitizers.
- QNX ARM builds and captured-runtime dependency/symbol audits accompany the private package. Existing Python and32/64-bit native suites remain included.

## Packaging and installation boundary

The private package contains compiled QNX candidates, the measured graph profile, source-manifest hashes and temporary launch scripts. Captured OEM support-model values stay in the private Drive artifact, not GitHub. No SDK, license material or factory binaries are distributed with source.

`deployment/run-isolated-handoff-selftest.sh` preloads the hook only into the fake test program in a private `/dev/shmem` directory. `deployment/run-parked-candidate.sh` runs the direct worker for30seconds with manual stopped-guidance confirmation. These are staged tests, not an autostart installer. The experimental hook has NOT been loaded into `NavNBTEvoController`, and no factory launch configuration was changed.

Do not install unattended v1 yet. Remaining acceptance requirements are: isolated QNX hook ABI test; direct head-unit RPM route and runtime timing; real factory pre-send integration/coverage and clean handoff; visual removal/factory behavior; crash/transport-loss policy; validated shift thresholds; and startup/rollback behavior. Automatic resume after guidance is intentionally absent: a completed handoff stops the worker rather than treating an idle packet as permission to reclaim shared state.

There is no need to collect more broad captures for this candidate. The next hardware work, when ready, is executable acceptance testing with explicit outcomes. The isolated ABI test must pass before considering any factory-process integration. Do not present the remaining acceptance work as already completed offline.
