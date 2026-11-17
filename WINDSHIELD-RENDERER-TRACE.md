> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

> Follow-up: [SESSION-CONTRACT.md](SESSION-CONTRACT.md) now identifies create/initialize/dispose formats and factory sink selection. It does not establish independent ownership or remote expiry.

# Windshield renderer investigation — 16 November 2026

Status: **live drawing test blocked; no car session requested.** The new evidence identifies the producer and two consumer families of the saved drawing buffers. It does not establish an independently owned windshield surface.

## Evidence chain

Addresses apply only to the captured binaries. The private evidence package includes SHA256-labelled region extractions; OEM bytes, route data and buffer snapshots are excluded from this repository.

| Stage | Static evidence | Consequence |
|---|---|---|
| Displayable registration provider | NavigationFully 0x1eb6ec reads the current session at object+0x134, rejects negative sessions or an unready manager, and constructs event 0x60eef0 with user ID, view type and dimensions. | DNAVIManeuverView registration creates a navigation displayable; it is not itself a cluster-side surface allocation. |
| Displayable factory | 0x6145dc calls 0x88249c. Factory rejects type 2, selects separate paths for types 1 and 3, and constructs a displayable at 0x881d48. Type 3 reaches command-only initialization 0x8811e4. | Internal view-type enums must not be substituted for DisplaySink selection or physical screen IDs. |
| Buffer identity | Displayable constructor stores its ID at +4. 0x881218 passes that value to command-output constructor 0x880dec, which stores it at +4. 0x880050 rotates an index at +0x3c; 0x8800a8 formats `GVCommand_%d_%d` from ID and slot. Shared-memory resize appends size at 0x88d06c. | First number = displayable ID; second = ring slot. Neither establishes the windshield destination. |
| Buffer lifecycle | NavigationFully store 0x88d210 requires header+8 == 0xfffffffe; after locking, 0x88d234 sets the supplied sequence and copies payload after 12 bytes. Controller consumers 0xabe6f4, 0xac0cfc and 0xac3270 set -2 after parsing. | All 99 snapshots have reusable-state sequence -2. Retained payload is useful static evidence, but not an active-frame claim. |
| Modern navigation consumer | Controller parser 0xd4b434 is directly called at 0xabe6e0, 0xac0cd8, 0xac325c. These DisplayableData handlers check event sequence and length, lock, parse buffer+12, update model data via 0xa9e22c and release the buffer. RIC maneuver-based subjob identity is anchored at 0xabdf14/0xabe874. | The newer 0x700xx chunks do have a controller consumer. The earlier MOST shape parser at 0xd3c6e4 is not the only parser. |
| Chunk semantics | Type-name dispatch 0xd43504..0xd43818 and modern parser diagnostics identify maneuver state, intersection, CCP, distance and picture-in-picture records. The type-name dispatch is a naming function, not itself the decoder. | These are structured navigation records; not generic line/circle commands. |
| Label data | 0x76d3ac recognizes 0x80001 and logs LabelContainer; 0x76d204 decodes route-handle/hint/path-position fields. Class strings identify CGuidanceViewerLabelsParser. | Large label buffers are not demonstrated bitmap framebuffers or free drawing canvases. |
| Image resources | Static maneuver job builders 0xaa7798 (SVG), 0xaa78a0 (bitmap), 0xaa79a8 (picture-in-picture) search resource records and append model objects. | A model/resource route exists in code, but accepted image format, windshield routing, distinct client ownership and cleanup are unproven. |

The existing configuration/packet evidence maps B006 guidance and B009 DisplaySink to BMW.Kombi at 160.48.199.96. Combining that with these static consumers supports a structured navigation-model route toward the cluster. It does **not** identify the cluster's final rasterizer or prove arbitrary custom content can coexist with factory overlays. The cluster renderer executable has not been identified in the captured head-unit binaries.

## Reproducible saved-buffer inspection

`python3 tools/inspect_gv_buffer.py /private/GVCommand_17_0_5132.0.bin`

The tool reports the first retained chunk only by default. Full parsing requires both the independent DisplayableData event length (including its 12-byte shared header) and sequence:

`python3 tools/inspect_gv_buffer.py snapshot.bin --event-bytes LENGTH --event-sequence SEQUENCE`

Reusable buffers, sequence mismatch, truncation and oversized chunks are rejected for event-bounded parsing. An event match still does not prove an atomic snapshot, ownership or windshield destination. No remote reads, replay or writes are implemented.

All 99 private snapshots inspected successfully: 26 HGPictureInPicture, 28 LabelContainer, 18 ManeuverHighCCP, 6 LGIntersection, 5 ManeuverState, 5 CCPInfo, 4 LGRoundAbout, 3 DistanceToManeuver, 2 ManeuverDistance, 2 Bargraph first chunks. These are first-chunk counts, not complete message/frame counts. The full Python/host suite passes 82 tests, including 10 new buffer-boundary/lifecycle tests.

## Concrete test target and entry criteria

The intended test is one static, uniquely identifiable marker on an **independently allocated** windshield destination, followed by explicit release and confirmed disappearance. This is a test specification, not an executable vehicle test. Do not use factory handles 0x64/0xc8, overwrite factory navigation objects, or replay retained shared-memory contents.

Before asking for car time, the implementation must have:

1. A traced request/response contract that allocates a distinct RIC session/resource and identifies ownership. A DNAVI displayable ID alone is insufficient.
2. A verified destination-selection contract for the windshield. The observed DisplaySink value 1 and resolution pair 460/237 are not sufficient.
3. An accepted primitive or image-resource schema with bounded payload and dimensions. SVG/bitmap builder names alone are insufficient.
4. A traced release path and a remote lifetime/expiry mechanism. A local process timeout does not remove a persistent remote image.
5. A host-tested sender and decoder with bounds, response matching, failure handling and evidence logging; target loader/import checks; no automatic retries that create duplicate sessions.

Once those entry criteria are met, the parked test sequence is: establish normal factory HUD; allocate one owned test object; draw one stationary marker within verified bounds; verify windshield visibility; release it and verify disappearance; verify factory speed/nav/radio remain functional. Failure of ownership, routing or release is a failed test, not a reason to substitute a factory object. No engine revving or driving is needed. The timing/region limits must be selected from the verified lifetime and geometry contract before execution.

## Remaining offline work

Trace the RIC create/release serializers and result handling to the external cluster session, the mapping from DisplaySink notifications into the selected IC/HUD client, and SVG/bitmap resource model serialization and references. Determine whether the independent-session contract actually supports a second overlay. If that capability exists only in cluster firmware or is rejected by the interface, report that boundary; do not hide it behind another generic capture request.
