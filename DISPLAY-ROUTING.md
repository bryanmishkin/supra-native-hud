# Displayable-session routing trace — 16 November 2026

## What is now established statically
In the captured NavNBTEvoController, registration, display routing and drawing are separate stages. The trace reaches a concrete shape renderer, but has not established that this renderer is the active Ethernet windshield backend or available to a new application.

All addresses apply only to binary SHA256 71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a. Object offsets and internal enums below are not network identifiers or commands to send.

| Stage | Evidence |
| --- | --- |
| Register result | At 0x6df12c the handler compares the returned request pointer with the pending pointer at object+0x70. The matched path stores result word 0 at +0x6c and word 1 at +0x68. Logging identifies these as displayable and MoCCA session values respectively. |
| Display selection | The handler reads fields +0x10c and +0x110, previously logged as IC and HUD display selections. Its view-type availability diagnostics are distinct from session IDs. |
| Sink switching | The handler around 0xa7a2a4/0xa7a2d4 changes a flag on a referenced object and logs Kombi-to-HUD versus HUD-to-Kombi. Both paths still check displayable-session objects before continuing. These are internal state transitions, not evidence that the app can request them. |
| Data routing | The DisplayableData handler around 0x6dd39c selects a receiver and frame value using object+0x114 and maneuver/view type. It checks receiver availability and switching maneuver/view identity before calling 0x776cf8. Rejected data follows the shared-memory release path at 0x774574. |
| Command-data buffer | 0x776cf8 maps a named data region, checks a header sequence at buffer+8 against the data sequence, locks the buffer and passes bytes after a 12-byte header to 0xd3c6e4. It then dispatches through receiver vtable slot +0x38. Exact buffer format beyond those observed accesses remains unresolved; no shared-memory writes were attempted. |
| Concrete receiver | Constructor 0x77c590 stores vtable address 0xfafad8 at the object base. Its logging identifies CIcHudComm_TF11_13. Table slot +0x38 contains 0x77ce68, resolving this receiver's callback without guessing from strings alone. |
| Shape handling | Callback 0x77ce68 checks supported top frames, processes lists of polylines/polygons/circles and calls helpers 0x77b390, 0x77b2d4 and 0x77b1e0. The polyline helper reaches 0x777f5c through 0x77b4a0, passing point-related data; the recipient logs polygon-instance/item/type/point fields. The callback also reaches packetizer flush/frame-switch handling. |

This is a real internal drawing path. It is not a demonstrated independent tachometer surface. The binary contains multiple vehicle variants; the previously traced Ethernet coding branch skips the MOST guidance initializer. We must not infer that an internal drawing implementation is active merely because its code and vtable are present.

## Checks that did not resolve the missing link
Byte-string searches of captured libCoreFramework.A.so, libAppFramework.A.so, libSysMoCCAFrameworkSharedSo.cpp-ne.so.11 and NBTCarHU found none of the searched DNAVIManeuverView/RegisterDisplayableSession/BMW.IC.Guidance/HeadUp/HUD names. This narrow negative search does not prove those binaries have no relevant indirect behavior. Existing captured configuration text also lacks the provider binding.

The actual-car SOME/IP captures prove factory navigation and radio model exchanges, but contain no initial allocation handshake for those services. There is still no established mapping from a DNAVI displayable/MoCCA session to an independently owned 0xB006/0xB00E object or windshield region. In particular, do not substitute session IDs, frame selectors, model handles or vtable offsets for one another.

## Source work completed
Added tools/trace_arm_region.py for reproducible, bounded, read-only extraction of ARM ELF regions or word tables. It translates virtual addresses through file-backed load segments, annotates PC-relative word loads and possible strings, records the binary hash, and reports how many bytes were decoded. It does not execute input or infer reachability. Disassembly stops at undecodable data; literal pools can look like instructions, so callers must choose and review code regions. Thumb is unsupported.

Install the pinned static-analysis requirements into an isolated environment, then use:

```sh
python tools/trace_arm_region.py /private/NavNBTEvoController --start 0x77c590 --bytes 40
python tools/trace_arm_region.py /private/NavNBTEvoController --start 0xfafad8 --bytes 80 --words
```

All 43 Python/host tests pass, including synthetic ARM ELF literal translation, word-table extraction, architecture rejection and file-backed boundary checks. No captured OEM binary or route data is included in GitHub tests. The app's live-drawing behavior remains unchanged; no speculative backend was added.

## Remaining work for an independent surface
Identify the active provider and binding for ManeuverView.DNAVIManeuverView; recover the concrete renderer and transport selected on this Supra; establish client registration permissions, a distinct cluster-side allocation, windshield destination, overlay priority, lifetime/release and bounded update timing. Current evidence can support further static inspection of the command parser and transport helpers. It cannot establish the missing runtime mapping by itself. A later targeted passive initialization/configuration capture may be needed if that mapping is outside the captured binaries; no new car session is requested now.
