# MOST/DSI service inventory: 2026 Supra J29 (research baseline)

**Status:** Evidence inventory only, started 2026-11-18. This is NOT a complete service map, a decoded firmware specification, or authorization to transmit drawing commands. Preserve installed [V1 baseline](V1-BASELINE.md); research must not alter its worker, supervisor, resources, factory interfaces, startup or rollback.

## Identity and documentation boundaries

- Reference car: 2026 Toyota GR Supra 3.0 Premium manual; NBT Evo / iDrive 6; QNX 6.5 ARM32; navigation software identifier `NBTevo_T24081I`.
- The latter is labeled a **Navigation Version** by [NBT-AAD's compatibility list](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/main/requirements.md). It is not a complete QNX/HMI/cluster binary manifest, nor an authenticated OEM interface document. NBT-AAD lists this identifier as tested on a **2024 J29**; it does not assert MOST HUDTerminal drawing works there.
- [st1ng's CarPlay Advanced](https://github.com/st1ng/nbtevo-carplay-advanced/blob/main/README.md) documents *two different* paths: F-series MOST `HUDTerminal` polygon/text operations, and G-series/J29 Ethernet KOMBI route guidance over SOME/IP. CarPlay HUD guidance working on a J29 is therefore not evidence of direct MOST polygon drawing.
- [Ghackt's installer](https://github.com/ghackt/Carplay-advanced-installer/blob/main/README.md) packages/installs st1ng's payload and reports J29/A90 testing; that does not independently identify a MOST HUDTerminal provider on the J29.
- Public code and community documentation exist. No publicly accessible, build-exact OEM `NBTevo_T24081I` MOST service schema, routing table, and HUD object-ownership specification has been verified in this research.

## What this *specific car* has demonstrated

Derived from [actual-car validation](../CAR-VALIDATION.md), [renderer investigation](../RENDERER-TRANSPORT.md), and [current architecture](APP-ARCHITECTURE.md). The raw vehicle registry/binary captures are **private** and were not added to GitHub.

| MOST FBlock / instance | Function or clue | Source / status | Evidence limit |
| --- | --- | --- | --- |
| `0x05/00` Vehicle | `EngineSpeed2`, function `0x0CD0`; registry provider `0x5000` | **Proven in installed V1** | Read-only 2-byte big-endian quarter-RPM GET/STATUS is live; this proves MOST telemetry, **not** HUD drawing. |
| `0x40/01` | Radio-window traffic from source `0x1019` | **Observed header pattern** | Semantics, payload, destination and relationship to HUD are unverified. |
| `0x15/02` | Radio-window traffic from source `0x5000` | **Observed header pattern** | Upstream NBT-AAD interprets `0x15/02` as steering-wheel messages on a J29; mapping **on this car** is not established by the historical headers alone. |
| `0x82/00` HUDTerminal | Older BMW/MINI polygon/text/visibility drawing service | **Not advertised/observed** in the surveyed windows | 112-entry registry in baseline, radio and navigation windows had no `0x82/00`; broad header observer saw no `0x82`. Negative coverage is bounded to those windows/methods; does not prove no possible interface. |
| `0x81/**` | Constructor field `0x81` in static shape-rendering code (meaning unknown) | **Not advertised/observed** in checked snapshots | Do not equate that field with a genuine FBlock ID without proof. |
| `0x82/02` | Second HUDTerminal documented by st1ng on certain older cars | **Unverified on reference J29** | No provider/instance/address/ownership established. |

### Survey coverage and limits

Historical 2026-11-16 registry/observer session: 112 registry entries each; 1,927 received messages in normal HUD window, 2,998 in radio-selector window, 1,953 in navigation-instruction window; 99/143/108 distinct header patterns, respectively. Registry and broad-header observer did not show `0x82/00`. Observation kept bounded headers and counts, not all request payloads. This was not a full startup service registration trace. Record exact captures privately before drawing further conclusions.

## Active HUD transport already proved

The accepted V1 consumes `EngineSpeed2` over MOST/DSI and uploads a 150x36 bitmap through the cluster's **Ethernet** guidance renderer. The target's measured endpoint is `160.48.199.96:30502`, SOME/IP service `0xB006`, instance 200; the shared factory radio/list path is `0xB00E`, instance 100. These are measured *reference-car* values, not defaults for other vehicles. Details and ownership/fail-closed constraints: [architecture](APP-ARCHITECTURE.md), [baseline](V1-BASELINE.md).

Offline navigation binary review identified `HUDTerminal.ImageAddPolygonCall` and a native MOST packetizer, **but also** a coding-controlled Ethernet KOMBI branch. Linked code can exist without being the active cluster transport. See [HUD path review](../HUD-PATH-REVIEW.md), [renderer transport](../RENDERER-TRANSPORT.md).

## Public comparison and protocol leads (NOT confirmed on this Supra)

- [st1ng MOST HUD renderer](https://github.com/st1ng/nbtevo-carplay-advanced/blob/main/src/hud.h): implementation and formats of `HUDTerminal` vector/text/visibility commands.
- [st1ng engineering notes](https://github.com/st1ng/nbtevo-carplay-advanced/blob/main/AGENTS.md): explicit MOST vs Ethernet KOMBI selection and transport conditions. Its `hud_probe.sh` can **send drawing/visibility commands**; do not run it as a passive diagnostic or assume its handles belong to the J29.
- [Sq00ky's MOST registry decoder](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/main/milestone-7/src/most/registry.hpp): definition of advertised FBlock/instance-to-node records.
- [F60 field report, HUDTerminal `0x82/00`](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/issues/176): a positive comparison where a MOST registry **does** advertise `0x82/00`, along with actual draw-function traffic and acknowledgement quirks. Do not transfer the F60's node, handle, transmission type or geometry to the Supra.
- [NBT-AAD J29 KOMBI client](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/main/milestone-7/src/cluster/j29_client.hpp): route-guidance service over Ethernet, deliberately does not create/dispose factory guidance objects.

## Next documentation work (read-only first)

1. **Build complete inventory from saved private evidence:** Parse every recorded registry entry `{node, fblock, instance}` in the three 2026-11-16 windows, with source hashes, capture date, boot state, and differences across windows. List every entry, not just `0x82`. Keep any vehicle-identifying/private data off GitHub.
2. **Correlate observed MOST messages:** For each provider and function, preserve `source/destination/fblock/instance/function/op/class/count`, operating state, and whether telemetry or command semantics are proven. Do not infer undocumented payloads. Add a *known / inferred / unknown* status for every mapping.
3. **Verify active renderer selection offline:** Resolve actual runtime configuration/coding and provider binding of Ethernet KOMBI versus MOST HUDTerminal using existing captured factory binaries and configuration before any new vehicle session. The historical `CIcHudComm_TF11_13` reference alone is not a runtime binding.
4. **Compare apples to apples with other Supra owners:** Request exact navigation version **and** HMI/build identifiers, MOST registry presence for `0x82/00` and `0x82/02`, cluster hardware/coding, and a log proving whether HUD vectors were sent over MOST or route data was sent over `0xB006`. A screenshot of HUD navigation cannot distinguish transport.
5. **Decision gate:** If no registered MOST drawing provider appears at initialization, document the negative evidence and investigate additional Ethernet graphics/display/session interfaces without modifying V1. Any future sender requires independently verified ownership, geometry, acknowledgement timing, factory priority and rollback. No trial drawing commands on speculative handles.

## Key conclusion

**MOST exists and is accessible on this Supra, as proven by live RPM. A separate direct MOST HUD drawing service is not yet proven and the expected FBlock 0x82/00 was not seen.** Current evidence more strongly supports an active Ethernet KOMBI graphics path. This may reflect hardware topology or runtime coding, not firmware removing a capability. The actual reason is not yet established.

_Last checked against public source and current repo evidence: 2026-11-18._
