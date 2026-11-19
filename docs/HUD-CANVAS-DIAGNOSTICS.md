# HUD canvas and MOST/DSI investigation kit

19 November 2026. Offline prepared; no vehicle connection or changes. Owner selected our existing MOST/DSI tools. Goal: an evidence-backed interface map and a reproducible pixel-routing test. Complete reverse engineering is not claimed or guaranteed by one capture.

## Current interface map

| Layer | Established | Still to establish |
| --- | --- | --- |
| MOST/DSI | Factory RPM 05/00, function 0cd0; registry observer available | Whether a relevant HUD provider is exposed and what messages are delivered to a separate observer; absence is not proof of no route |
| Working V1 drawing | B006 shared session 200, image slots 01000008/09, 150×36 tested | Larger supported image/visible bounds, independent ownership, clipping and scaling |
| PiP producer | Captured HU Screen/LayerManager/output-driver chain and native metadata encoding | Receiver's association of producer endpoint/stream with selected display |
| DisplaySink B009 | Factory renewals/ACKs, prior 460×237 selection 1; unsubscribe associated with guidance stop | Initial handshake on a fresh factory session; what causes a windshield destination selection; whether a separate producer can coexist |
| HUD visibility | Owner's Navigation checkbox hides navigation and tach | Exact receiving component applying the visibility control |
| Height rectangle | Owner sees broad outline; recorded while V1 sends its own bitmaps | Source of outline and whether its bounds are accessible to applications; not a proven PiP surface |
| Cleanup | Existing V1 owned-image removal and factory handoff tested | New producer's complete lifecycle and ownership before any larger-image injection |

## Packaged tools

- `tools/capture_most_snapshot.py`: offline plan by default. Creates a unique RAM directory, verifies the pinned observer bytes, observes 15 seconds with a native 20-second deadline, retrieves registry/header results, checks process/file removal and all 15 V1 hashes plus permanent faults. No coding or target function requests. It does create a temporary DSI client and subscriptions; do not call it a zero-interaction sniffer.
- Existing `tools/consolidated_capture.py --record-only`: 120-second native TCP/UDP capture including cluster traffic and SD; exact binary pinned in the prior PiP kit.
- `tools/audit_pip_discovery.py`: SD subscription/ACK/unsubscribe timeline. `tools/audit_pip_binding.py`: known TCP selection/image-reference shapes. Raw packets remain necessary for unknown variants.
- `tools/capture_output_driver.py`: broader bounded read-only driver/configuration capture if target identity differs; do not repeatedly retrieve unchanged OEM binaries.

The MOST observer host regression checks registry decoding, malformed/overflow handling, reconnect behavior and refusal to send target requests. ARM ELF imports and DSI exports pass static checks against saved target libraries. These checks do not prove every callback ABI, current vehicle state or server-side registration cleanup. The observer's upstream client has no stop/join contract; native process exit is bounded, but server registration release needs explicit evidence before repeated automated loops.

## Concrete parked sequence, in one visit when requested

First collect current V1 permanent faults and RAM logs before resets. Verify baseline and observer identity. No live commands are required during driving.

1. Run one MOST snapshot in the ordinary HUD state. Inspect result for valid registry, zero sends/drops and clean process exit. Do not loop if link/cleanup is uncertain.
2. Start Ethernet recording **before** starting factory guidance. Once READY, start guidance and leave it visible for about 30 seconds; stop guidance while the same recording still runs. Save owner observations with command-send and reply times rather than pretending the reply timestamp is the physical click. Capture state descriptors in their own directories. This targets session creation and removal that the last checkbox recording began too late to observe.
3. Use a separate recording for radio selector open/close, starting recording first. Do not squeeze navigation, radio and height into one 120-second window. Keep the owner in the car until analysis verifies whether the relevant transition was actually captured; do not repeat a transition solely because a narrow decoder is empty.
4. Height overlay is a distinct optional capture only if it can answer a remaining specific question after offline comparison; its completed 18 November recording is already retained. Do not repeat it just to collect more packets.
5. Additional MOST snapshots are conditional on initial clean behavior and a concrete registry/provider change to test. The current observer does not collect payloads or authorize broad diagnostic probing. A general MOST sniffer would require a different verified mechanism.
6. Restore original owner settings and stop guidance. Verify V1 return, component hashes, fault comparison and recorder/client process cleanup. Preserve raw data privately and publish redacted derived findings.

The native recorder ends after 120 seconds. If setup uses most of the window, do not start a transition near its end; start a new bounded window before asking the owner to act. The earlier 4-phase single-window run was incomplete and is not the template for this procedure.

## Commands

Run from the source repository with the existing analysis Python (pyelftools). Set `PY`, `HEAD`, `LOCAL`, `KNOWN_HOSTS`, `KIT`, `OUT` to verified absolute session paths/addresses. `OUT` must not exist. Optional existing SSH master: add `--socket /verified/socket`.

```sh
"$PY" tools/capture_most_snapshot.py
"$PY" tools/capture_most_snapshot.py --execute --head "$HEAD" --local "$LOCAL" --known-hosts "$KNOWN_HOSTS" --binary "$KIT/supra-registry-observer-qnx" --sha256 "$OBSERVER_SHA256" --output "$OUT"
```

`OBSERVER_SHA256` comes from the supplied manifest, checked against the actual file before use. Do not substitute a binary merely because its name matches. Output `most-result.json` distinguishes complete observation from unsupported bus-wide/registration-cleanup claims.

## What counts as concrete canvas proof

For each proposed path retain: provider/client identities; subscription and negotiated destination; session/handle/resource IDs; dimensions/format/stride; pixel producer and transport; visibility/model reference; commit response; owner-confirmed distinct custom marker; withdrawal, resource absence and factory/V1 restoration. ACKs, a factory arrow, a local Screen window, or the height outline alone do not satisfy this chain.

A new active marker is gated on this ownership/routing evidence and a bounded cleanup implementation. No fuzzing, arbitrary MOST sends, factory endpoint impersonation, new aliases, firmware writes or changes to V1 are included in this kit. The failed PiP marker runner remains retired.

## Offline work still possible

Correlate retained initial subscription windows and captured HU code; decode unknown SD bundles without guessing; separate factory vector updates from V1 bitmaps and unrelated NMEA traffic; map methods and resource lifetimes; determine whether a new observer truly receives traffic beyond its registry; identify matching receiver implementation if available. Record unresolved items explicitly rather than labeling the interface fully reverse engineered.
