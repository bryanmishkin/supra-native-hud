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


## Completed forensic inventory from the actual private capture archive (18 November 2026)

**Status: offline analysis completed. No vehicle connection, transmission, or change to installed V1.** This section supersedes the earlier statement that the full registry had not yet been decoded. The three exact schema-2 outputs were recovered from the owner's private \`Supra-HUD-Diagnostics-2026-11-16.zip\` archive, under \`car-session-validation-2026-11-16/discovery-{baseline,radio,navigation}.log\`. The archived lines contain a DSI loader preamble followed by one observer JSON object. The data were parsed offline; the raw source and full address/headers report remain **private**, not committed.

| Capture | Registered FBlock/instance keys | Distinct FBlocks | Messages | Distinct header patterns | RPM status \`0x05/00:0x0CD0\` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Normal HUD | 112 | 52 | 1,927 | 99 | 148 |
| Radio selector | 112 | 52 | 2,998 | 143 | 148 |
| Navigation guidance | 112 | 52 | 1,953 | 108 | 148 |

All 112 registry service-to-node mappings matched **exactly** in all three windows. Each recorder reported zero sent HUD commands, zero dropped headers/snapshots and no captured message payloads. This is a strong *bounded* observation, not proof of comprehensive boot-time enumeration.

### Concrete cross-checks

- **Verified EngineSpeed2:** registry key \`0x0500\` (Vehicle FBlock \`0x05\`, instance 0) maps to provider node \`0x5000\` in all three captures. Each capture includes 148 outgoing factory \`STATUS\` messages with function \`0x0CD0\`, from \`0x5000\` to \`0x2021\`. The separately tested installed worker asks read-only GET \`0x0CD0\` from \`0x5000\` and decodes unsigned big-endian quarter RPM. The \`EngineSpeed2\` name and numeric binding are grounded in the captured HMI object/vtable analysis and our car's runtime, **not a claimed universal published BMW MOST definition**.
- **Other Vehicle functions observed but not named:** \`0x0622\`, \`0x0623\`, \`0x0624\`, \`0x0CA1\`, \`0x0CA2\`, \`0x050C\`, \`0x0628\`, \`0x021F\`, \`0x0902\`, and more. These are **not** evidence that boost pressure is exposed over MOST. Their names, units, conversion, and source samples are **unknown** without separate code/payload attribution. Do not query guessed IDs.
- **Other advertised services:** \`0x1502\`, \`0x150C\`, \`0x2000\`, \`0x4001\` and \`0x5200\` are all in the registry. Upstream NBT-AAD source identifies \`0x1502\` as an MFL control interface and \`0x2000\` as AudioMaster on its targets; this car's exact function semantics require correlation. Radio interactions increased observed \`0x4001\` traffic, but that correlation alone does not identify a protocol.
- **HUDTerminal:** neither \`0x8200\` nor \`0x8202\` was advertised; no messages with FBlock byte \`0x82\` were seen. Note that the observer's JSON \`"fblock":82\` is **decimal 82, hexadecimal \`0x52\`**, which **is** registered at \`0x2021\`. Do not misread this as a discovered HUDTerminal.
- **BOOST is not yet mapped to MOST:** SAE J1979/OBD service 01 PIDs \`0x0B\` (manifold absolute pressure), \`0x33\` (barometric pressure), \`0x70\` (boost pressure control) and \`0x87\` (intake manifold absolute pressure) are distinct **ECU diagnostic identifiers**, not MOST function codes. Support and units must be checked on the reference vehicle before considering a display feed. Factory engine pressure can be measured at different physical locations, so calling any one pressure “boost PSI” requires a defined gauge-pressure calculation.

### Archived observations, source hashes

| Window | SHA-256 of **entire log**, including DSI preamble |
| --- | --- |
| baseline | \`ca39b260ab40f1cd0aa07c2012731b70c93648db81cffd732bfb5c9a95700944\` |
| radio | \`de1b651ede019c26c0727343d8b7d8e504992e5b7c28f310df74eca106cb72a0\` |
| navigation | \`1b1f550a39773a39702fa856f1dfe4762f0082614a1836788a26a78685bd59d6\` |

A reusable **offline-only**, validated \`most_service_mapper.py\` and the complete private CSV and Markdown maps were produced for the owner in the 2026-11-18 analysis artifact. The script accepts exact schema-2 observer logs/ZIP; it does not open a socket, send commands, probe an ECU, or install anything. Any distribution of the raw archive/report should be deliberate, as source logs may contain vehicle identifiers and proprietary data.

### Prioritized follow-up without sending commands

1. **Use the full inventory first:** We now know all advertised FBlocks from these windows. Correlate the \`0x05/00\` observed function IDs to names in existing captured HMI/runtime code before considering another car session. Avoid broad blind GET scanning.
2. **Separate read-only discovery channels:** To identify additional telemetry, use passive observation of factory functions and/or narrowly allowlisted, source-backed GETs against registered providers. New on-car observations must be separately reviewed, bounded and hashed. Never spray functions, query nonexistent providers, or send a mutable setter/actuator/graphics command as “discovery”.
3. **Boost:** Independently validate any DME/OBD absolute pressure signal and atmospheric reference, including sensor location, while parked under controlled conditions. No boost value is enabled for V1 and no on-car pressure query was executed as part of this analysis.
4. **HUD drawing:** The missing \`0x82\` registry remains meaningful. A MOST-based polygon sender is not authorized by this inventory. Continue offline trace of factory transport selection and bound display providers; preserve V1 factory handoff and cleanup rules.

