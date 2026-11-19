# V1-to-PIP resource parity audit (offline, 2026-11-18)

**Goal:** Reuse the vehicle-verified V1 display protocol for a larger visual resource, with picture-in-picture (PiP) as the candidate. This is **not** a successful PIP drawing demonstration or authorization to write to the car. Keep the exact accepted V1 runtime, startup hooks, lease arbitration, resource slots and rollback untouched.

## Key conclusion: same framework, type-specific serialization

The captured factory code explicitly routes resource building through one common dispatcher:
- `0xaa7ab8` in the captured NavNBTEvoController calls SVG builder `0xaa7798`, then bitmap builder `0xaa78a0`, then **PiP builder `0xaa79a8`**, accepting the first successful match (saved `windshield-offline-trace/model-pip-builder.json`).
- Actual `0xB006` create-response for shared handle **200** advertises both bitmap **configuration tag 33 / resource type 1** and PiP **configuration tag 35 / resource type 2**. This is *one negotiated resource-management framework*, not evidence of separate head-unit networking.
- The factory executable has distinct logging/functions **`sendBitmapImageResource`** and **`sendPIPElementResource`** and **`sendPiPElement`**, plus `setPIPElementForICHUD`, `setPIPElementForCID`, `sendAttachToCommandPIPICHUD` and `sendAttachToCommandPIPCID`. ARM call-site tracing additionally proves both typed senders call the common `0xAB3934` resource-upload dispatcher. Runtime ICHUD routing and exact visible binding are not thereby proven.
- **Do not assume that a different resource type changes SOME/IP service or protocol.** Equally, do not claim V1's bitmap variant-2 payload is valid for PiP without tracing the PiP serializer.

## Exact side-by-side evidence

| Stage | V1: known good on actual car | PiP: existing evidence | Parity confidence |
|---|---|---|---|
| Cluster destination | `160.48.199.96:30502`, SOME/IP `0xB006` | PiP type-35 config returned by `0xB006` handle-200 create | Same service/config surface, **confirmed** |
| Session | Factory shared handle `200`; no instance disposal | Config returned with handle `200` | Same negotiated shared context, **confirmed** |
| Resource allocation | Type **1** bitmap, ten slots `0x01000000..09` | Type **2** PiP, five slots `0x02000000..04` | Same config-array allocation pattern, **confirmed** |
| Size / format | `150x36`, RLE32; color swap measured | Config tag35 `23020000000502000000014001400100` -> two `0x0140` values (320,320); last two bytes 01,00 | PiP max resolution fields **confirmed**; encoding semantics need trace |
| Builder | Factory bitmap builder `0xaa78a0` | PiP builder `0xaa79a8` called by same dispatcher | **Confirmed common dispatcher** |
| Upload | B006 method 3 tag2 bitmap with type1, successful on car | Binary has `sendPIPElementResource` and `sendPiPElement`, but captured factory B006 method-3 sends are type3/tag4, *not* type2 | Same generic method-3 upload helper **statically proven**, PiP variant tag **3**; exact PiP payload layout **still needs decoding** |
| Visible binding | B006 method 14 / coming-road list type40, description + guidance models, successful live V1 | Binary has PiP-specific **ICHUD** and **CID** attach/element functions | Binding exists in compiled code; exact external wire reference **not mapped** |
| Projection | Visible V1 in windshield HUD and cluster | 52 archived GVCommand snapshots whose first chunk is `HGPictureInPicture`, five unique 12-byte first-chunk payloads | Source-stage PiP structures **observed**, remote projected PiP **not observed** |
| Cleanup | V1 removes model references and only its two bitmap resources, checks absent, coordinates factory handoff | B006 checkResource method2, disposeResource method8 likely reusable if PiP supported by instance; exact PiP ref removal not captured | No validated end-to-end PiP cleanup |

## Full actual-car configuration source

Private `Supra-HUD-Diagnostics-2026-11-16.zip`:
`car-drawing-trial-2026-11-16/profile-probe/001-response.bin` and `configuration-summary.json`.

- Bitmap tag 33: `21010000000a010000000096002400010000` (type 1, count 10, offset 0x01000000, 150 x 36, RLE32 flag)
- PiP tag 35: `23020000000502000000014001400100` (type 2, count 5, offset 0x02000000, two dimensions 320/320, trailing depth/packing bytes 1/0). The meaning of 1/0 needs the type35 consumer/serializer, not analogy to bitmap flags.
- This create test **returned the existing factory handle 200** after using BMW.IC.Guidance identification. That is not proof of independent ownership and must not be used to fabricate a new session.

## Source-stage PiP frames and limits

- Saved `GVCommand` first-chunk inspection: **52 snapshots**, **five unique first-chunk payloads**. The chunk kind is `0x70008` and its data is exactly **12 bytes**. Each .0/.1 copy can represent the same retained buffer; counting all 52 does not mean 52 distinct rendered frames.
- Source records contain 16-bit pairs consistent with **480 x 431** and **800 x 480**, adjacent to other values. Those are NOT proven physical HUD dimensions, bitmap upload dimensions or a PiP viewport without a decoded field schema and active routing.
- In the saved **144 reassembled SOME/IP stream files**, factory B006 method 3 occurs **six** times, all resource type 3 / variant 4. There are **no PiP resource-type-2 uploads** in those streams. No command-by-command link from a retained GVCommand first chunk to a cluster PiP frame has yet been established.
- Header logs alone do not carry pixel bytes or model references.

## Work that uses evidence, not new car captures

1. **Finish decoding PiP's typed payload**, now that the common method-3 resource sender and variant-3 dispatch are located. Follow `0xBB51E8` -> `0xBB5158` and nested writers, then compare their bytes and validation with V1's bitmap variant 2 (`0xBB63E8` -> `0xBB6350`). Work from saved binary, not inferred fields.
2. **Trace PiP visible attachment:** `setPIPElementForICHUD`, `sendAttachToCommandPIPICHUD`, `RIC_CRicDisplyableSessionForPiPComICHUD` and their CID counterparts; bind PiP resource ID to a *specific* model / sink / session and identify distinction between navigation data PiP and command display.
3. **Decode first-chunk 0x70008 fields** using the already captured `NavigationFully` producer and `NavNBTEvoController` consumer. The 12 bytes need a real structure mapping, not a dimension guess.
4. **Review V1 resource ownership rules** for type2: the type2 slots have not been granted to our app. A parked test must use a verified-free PiP slot, never disturb active factory PiP, and must include reference removal, disposal, absence check and factory priority.
5. After offline types and binding are proved, make a **separate, default-disabled, bounded parked PIP trial**; record ACKs, visual result, cleanup and ordinary factory HUD behavior. No integration into persistent V1 before acceptance.

## Distinction to preserve

The evidence supports the design hypothesis: **same cluster resource framework with separate resource-type serializers/bindings.** It does not support either extreme: that PiP is a completely unrelated display protocol, or that changing the hardcoded `150x36` and resource ID in V1 is sufficient to render a 320x320 image.


## Newly closed static question: the same resource-upload function (18 November 2026)

Independent offline ARM A32 branch-instruction decoding, on the previously captured and hashed `NavNBTEvoController`, establishes all **three typed factory resource senders call the same helper**:

| Sender | Typed variant constructor | Constructor tag | Branch to common helper | Helper |
|---|---|---:|---|---|
| PiP `sendPIPElementResource` | `0xAAFC2C` | **3** | `0xAB3C80` | `0xAB3934` |
| Bitmap `sendBitmapImageResource` | `0xAAFC48` | **2** | `0xAB3E40` | `0xAB3934` |
| SVG `sendSvgImage` | `0xAAFC64` | **1** | `0xAB3FE8` | `0xAB3934` |

Each variant constructor stores its tag as an ARM immediate before invoking a type-specific constructor. The serializer's variant dispatch chain includes: tag3 at `0xBBDC20` -> `0xBB51E8` -> `0xBB5158`; bitmap tag2 at `0xBBDC58` -> `0xBB63E8` -> `0xBB6350`. Both feed the common outer resource envelope. `0xAB3934` is the generic sender used by the documented B006 method-3 resource call. This is direct code evidence of **shared upload architecture**, not merely a similarity of naming.

The **remaining unknown is inside the PiP-specific variant-3 payload and how it is referenced by the ICHUD models**. We now have concrete function addresses for a narrow offline trace. This finding contradicts the earlier suggestion that PiP might require an unrelated network upload path; do not repeat generic interface discovery.


## Larger graphics spaces: exact saved-data routing audit (18 Nov 2026)

**Evidence reviewed:** private Supra-HUD-Diagnostics-2026-11-16.zip (actual cluster profile create response, three sets of retained GVCommand ring buffers, continuous SOME/IP recordings, captured NavNBTEvoController and NavigationFully). This is an offline evidence audit, not a new car experiment.

### Local producer/receiver and encoded sizes

- NavigationFully generates local GVCommand buffers, and NavNBTEvoController receives/decodes the modern 0x700xx command chunks before processing RIC models.
- First number in GVCommand_ID_slot filename is a local **displayable ID**; the next is its ring-buffer slot. These are not the B006 image resource IDs.
- GVCommand_11_1_5132.0.bin has first chunk 0x70008 (HGPictureInPicture), size 12, data hex 0002e001af01000102000000. Little-endian fields: u16 512, **480, 431**, 256; u32 2.
- GVCommand_9_1_5132.0.bin has the same 0x70008 chunk, data hex 00022003e001000102000000. Fields: u16 512, **800, 480**, 256; u32 2.
- The .0/.1 retained copies are paired duplicates; 52 stored PIP first-chunk copies do NOT mean 52 fresh PIP rendering events. Five different first-chunk payloads were retained. Each checked command buffer had reusable/free sequence 0xfffffffe, so presence during stopped, radio or navigation snapshots is not proof that frame had just been rendered.
- **Provisional:** 800x480 may be CID-family and 480x431 may be ICHUD-family geometry. Neither displayable ID has been bound to a specific physical destination by the retained bytes. These values are not verified full HUD panel geometry. Separately captured center HMI LayerManager is 1280x480.

### Targeting mechanisms found in actual NavNBTevoController firmware strings

- **ICHUD family:** highCCPPictureIC.getCenterPosition[0/1], PIPICSizeX/Y, setPIPElementForICHUD, sendAttachToCommandPIPICHUD, RIC_CRicDisplyableSessionForPiPComICHUD.
- **CID family:** highCCPPictureCID.getCenterPosition[0/1], RIC_PIP_SIZE_CID/_PAD[0/1], setPIPElementForCID, sendAttachToCommandPIPCID, RIC_CRicDisplyableSessionForPiPComCID.
- These are clear evidence that the factory PiP implementation has per-destination positioning and sizing paths. Exact numerical coordinates, placement rules, and the link from displayable ID 9/11 to those paths are still unverified.

### Same network/resource framework as V1, but different typed binding

- Working V1 uses 160.48.199.119 -> 160.48.199.96:30502 SOME/IP B006, shared handle 200; type-1 RLE32 bitmap 150x36, method 3 variant 2, reference through method 14 model type 40. Resource release/absence and factory priority are verified.
- The **actual same handle-200 create response** advertised PiP configuration tag 35, resource type 2, five IDs 0x02000000..0x02000004 and two 320 maximum-resolution values. A negotiated range is not five free or privately owned rendering surfaces.
- Captured ARM control flow shows PiP resource variant 3 and V1 bitmap variant 2 call a **common resource sender** at 0xAB3934, compatible with the B006 method-3 envelope. PiP type-specific serialization is at 0xBB51E8/0xBB5158, while bitmap uses 0xBB63E8/0xBB6350.
- Continuous factory recordings have **six** B006 method-3 upload requests, all type-3/variant-4, **zero type-2/variant-3 PiP uploads**. Thus the actual display-attachment network transaction is not in the saved recording.
- B009 DisplaySink is a separate port 30503 interface. Factory routing trace assigns selection 0=HUD, 1=Kombi for navigation. It does not grant an arbitrary PiP surface or identify CID.

### Precise next offline work (do not repeat registry discovery)

1. Decode the 0x70008 12-byte chunk using its NavigationFully producer and NavNBTevoController consumer. Find the actual displayable-ID-to-ICHUD/CID binding.
2. Trace sendPiPElement -> setPIPElementForICHUD -> sendAttachToCommandPIPICHUD to the exact B006 model method and resource reference, including center position and size.
3. Complete variant-3 typed payload decoding from 0xBB51E8 and negotiated depth/packing. Compare against the V1 typed bitmap sender rather than assuming identical bytes.
4. Prepare a **separate disabled-by-default** parked proof only after a checked type-2 slot, exact reference/removal contract and factory priority are established. Do not overwrite bitmap slots 8/9, factory PiP or current V1 deployment.

The manually repositioned factory HUD-height adjustment rectangle observed by the owner on November 18 is **not** the November 16 custom rectangle/cross; these raw November 16 buffer snapshots do not yet establish which software path drew the height-adjustment rectangle.

## Existing source links

- [V1 known-good wire encoder](../src/standalone_wire.cpp)
- [V1 actual custom-drawing result](../RLE32-LIVE-PROOF.md)
- [PiP resource builder trace](../RIC-BITMAP-RESOURCE.md)
- [Factory HUD rendering trace](../WINDSHIELD-RENDERER-TRACE.md)
- [Resource/instance negotiated configuration](../SESSION-CONTRACT.md)

*Private OEM bytes, raw vehicle data and PiP snapshots remain out of GitHub.*
