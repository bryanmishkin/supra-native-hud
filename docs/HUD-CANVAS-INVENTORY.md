# HUD canvas and displayable inventory: reference Supra

**Status (2026-11-18): evidence-mapped, no direct full-screen framebuffer proven.** This is an offline cross-reference of the *actual* November 16 captures and factory binaries. It preserves the installed [V1 baseline](V1-BASELINE.md); no car commands, coding or new install were performed. Private OEM bytes, location data and capture payloads remain outside GitHub.

## Central distinction

There are at least four different namespaces; none should be substituted for another:

1. **Factory displayable ID** in NavigationFully shared-memory GVCommand names, e.g. `GVCommand_9_1_5132.0.bin`. Here 9 identifies an internal displayable, 1 a ring-buffer slot. These IDs do **not** identify a KOMBI framebuffer or physical screen.
2. **Source-stage command buffer** (e.g. 5,132 or 125,466 bytes), which can contain graphics model records, labels or PIP records. A large allocation is not a raster canvas.
3. **Remote B006 resource IDs** negotiated inside factory shared instance **200**, e.g. V1 type-1 bitmap `0x01000008` and PIP type-2 slots `0x02000000..04`. A resource is not inherently visible, positioned, or privately owned.
4. **Display routing/sink:** the cluster at `160.48.199.96`, with `B006` guidance on TCP 30502 and `B009` DisplaySink on 30503. ICHUD and CID have separate named PIP handlers in the captured controller, but the full remote compositor and guaranteed lifetime contract are not yet established.

## All captured local factory displayable IDs

The actual archive contains **198 copies of GVCommand files**, corresponding to **99 retained source buffers with paired .0/.1 copies**. Group counts vary by normal/radio/navigation capture window. Buffer sequence `0xfffffffe` denotes reusable/free state, so presence in one window is not evidence a corresponding graphic was freshly drawn in that window.

| Local displayable ID | First-chunk families observed | Nominal buffer allocation | What can be inferred |
|---|---|---:|---|
| 1 | `0x80001` LabelContainer | 125,466 bytes | Large label/data container, **not** a proven pixel canvas |
| 3 | `0x80001` LabelContainer | 5,132 bytes | Another label/data source |
| 7 | `0x7000a`, `0x30001`, `0x70005`, `0x7000d` | 5,132 bytes | Navigation-related models |
| 9 | `0x70008` HGPictureInPicture | 5,132 bytes | Encoded 800/480 value pair in one retained record; physical sink unknown |
| 11 | `0x70008` HGPictureInPicture | 5,132 bytes | Encoded 480/431 value pair in one retained record; physical sink unknown |
| 17 | `0x70003`, `0x70001`, `0x7000e` | 5,132 bytes | Navigation-related models |
| 19 | `0x70005`, `0x10001`, `0x7000d` | 5,132 bytes | Navigation-related models |

Examples of actual *first-chunk* payloads:
- `GVCommand_9_1_5132.0.bin`: 0x70008, 12 bytes, `00022003e001000102000000`. Little-endian 16-bit words: 512, **800, 480**, 256, followed by u32 2.
- `GVCommand_11_1_5132.0.bin`: 0x70008, 12 bytes, `0002e001af01000102000000`. Words: 512, **480, 431**, 256, then u32 2.

These pairs are **not established as physical framebuffer sizes** or as active projection rectangles. The remaining field meanings and their binding to ICHUD/CID still require static producer/consumer tracing. Do not equate the observed 800x480 pair with the measured center HMI screen of 1280x480.

## Actual negotiated B006 resource/configuration family

The reference car returned **22 configuration entries** for shared factory handle 200. This is a complete inventory of that one captured create response, **not a universal list of all graphics resources or display surfaces in the vehicle**.

| Configuration tag | Resource/model kind | Negotiated range/count | Dimension clue | Classification |
|---|---|---|---|---|
| **33** | **Bitmap resource type 1** | 10 at `0x01000000` | **150x36**, RLE32 | **V1 working pixel image, verified** |
| **35** | **PiP resource type 2** | 5 at `0x02000000` | **320x320 maximum-resolution fields** | **Larger raster candidate; not projected by us** |
| **36** | **Text resource type 3** | 10 at `0x03000000` | Trailing `0x0028` (meaning not independently decoded) | Text, not a free raster |
| **30** | Coming-road/list model type 40 | 5 at `0x27000000` | Ends in `0x00960024` (150,36) | **V1 image reference model, not new canvas** |
| 32 | Model/resource type 7 | 2 at `0x07000000` | None proven | Unknown model |
| 3 | Model type 14 | 5 at `0x0E000000` | None proven | Unknown model |
| 2 | Model type 1 | 5 at `0x01000000` | None proven | Distinct model/config namespace; not automatically bitmap |
| 19 | Model type 7 | 5 at `0x07000000` | None proven | Unknown model |
| 14 | Model type 27 | 26 at `0x1B000000` | None proven | Unknown model |
| 1 | Generic config for types 3,5,49,10,13,30,34 | Counts 2-5 each | None proven | Models; do not call pixel surfaces |
| 4 | Model type 17 | 1 at `0x11000000` | None proven | Model |
| 21 | Model type 33 | 1 at `0x21000000` | None proven | V1 list state |
| 20 | Model type 32 | 1 at `0x20000000` | None proven | V1 maneuver list |
| 17 | Model type 15 | 5 at `0x0F000000` | None proven | V1 maneuver description |
| 18 | Model type 29 | 30 at `0x1D000000` | None proven | V1 supporting distance model |
| 27 | Model type 37 | 25 at `0x25000000` | None proven | Unknown model |

**Absent in this particular returned configuration:** composite bitmap config tag **34** and high-guiding image config tag **39**, even though their deserializers exist in firmware. Their existence in a binary is not proof the reference vehicle negotiated them for this session.

## Separately observed display-size/position clues

- A captured B009 DisplaySink event contains u16 pair **460/237** and an aspect-ratio field decoded by factory code; **the pair has not been independently established as full physical HUD raster dimensions**.
- The head-unit binary has separate PiP paths for **ICHUD** and **CID**, with named `PIPICSizeX/Y`, `highCCPPictureIC.getCenterPosition[0/1]`, `setPIPElementForICHUD`, `sendAttachToCommandPIPICHUD`, and corresponding CID variants. These show placement/sizing constructs in firmware, not a successful custom full-canvas draw.
- The manually raised/lowered *factory HUD-height-adjustment rectangle* observed by the owner on Nov 18 moves with the **entire optical projection**, and is **not** the stationary custom rectangle/cross that established V1. No matching Nov 18 raw command capture has been identified. Optical repositioning is not evidence of independent sprite XY control.
- Factory radio, speed and speed-limit graphics are additional visible outputs that may be composed by the cluster locally. Their presence demonstrates the HUD has other graphic paths, not that each is a writable B006 bitmap.

## What V1 proves and what full-canvas V2 still requires

**V1 proven:** factory EngineSpeed2 via MOST, bitmap type 1 `150x36`, B006 method 3 variant 2 upload, method 14 model-40 coming-road reference, visual display in HUD/cluster, checked resource removal, radio/navigation priority and accepted persistent operation. Preserve the installed exact baseline.

**Next most credible path:** PiP resource type 2, up to 320x320, delivered through the *same* B006 method-3 sender, but typed variant **3** (firmware `0xBB51E8`/`0xBB5158`). Bitmap, SVG and PiP all call common resource sender `0xAB3934`. Their inner encodings and visible model bindings are distinct.

**Critical missing bridge for FULL HUD canvas:** determine which displayable/sink is actually routed to the complete windshield compositor, its physical logical coordinate bounds, accepted PiP/image/vector content, size/position/z-order, and how to acquire and cleanly release a privately owned object without suppressing factory speed, speed limit, warning or assistance graphics. We have **not** proven that the HUD offers arbitrary full-frame overwrite, independent layering, or an API to recolor/reposition all built-in elements.

## Work order, without repeating data collection

1. Trace the already captured NavigationFully producer and NavNBTEvoController consumer of first chunk 0x70008, including the 12-byte field layout and what factory displayable IDs 9/11 correspond to. Cross-check against named ICHUD/CID attach handlers.
2. Trace factory PiP resource variant-3 serializer `0xBB51E8` and PiP model reference/attach sender, compare bytewise with proven V1 envelope. Enumerate element dimensions, center coordinates, visibility and cleanup.
3. For other candidate graphics models, investigate the named factory label, SVG, composite bitmap, bargraph and high-guiding structures; distinguish local source records from cluster allocations. Do not assume factory radio/speed/limit appears as a bitmap upload.
4. Correlate the B009 460/237 event, RIC 320x320 limit and local 480x431/800x480 values to actual ICHUD physical rendering bounds through code, *not* by conflating numeric sizes.
5. Only if a destination/resource binding and safe cleanup are established offline, prepare a **separate default-disabled parked test**. First draw a stationary known pattern in a verified available resource, determine clipping/placement with visual observation, and check restoration. Leave V1 installed/unchanged. Do not run a blind full-screen overwrite or replace factory warnings.

## Sources

- Private original capture: Supra-HUD-Diagnostics-2026-11-16.zip; `car-drawing-trial-2026-11-16/profile-probe/configuration-summary.json`; `car-session-consolidated-2026-11-16/live-draw/*/GVCommand_*.bin`; retained network recordings.
- [V1-to-PiP parity](V1-PIP-RESOURCE-PARITY.md)
- [V1 working result](../RLE32-LIVE-PROOF.md)
- [Factory drawing-buffer trace](../WINDSHIELD-RENDERER-TRACE.md)
- [RIC lifecycle](../SESSION-CONTRACT.md)
- [Display routing](../DISPLAY-ROUTING.md)
- [DisplaySink](../DISPLAYSINK-REVIEW.md)

*No raw vehicle captures, OEM code/binaries, or proprietary route data are included in this document.*
