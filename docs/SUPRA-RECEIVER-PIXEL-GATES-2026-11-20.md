# Supra receiver pixel gates — 20 November 2026

## Source and scope

The older Toyota J29 package contains the same SWFL IDs as the identified cluster, versions **004_000_003**, versus installed **008_000_000**. Its receiver runtime is ARM/INTEGRITY/Candera. This is receiver code, not the earlier unrelated MIPS reference or head-unit producer.

No package executable was run. Relevant CAB members were extracted by verified 7-Zip, checked against MSI sizes, decoded with bounded segment decompression, and all 16 inner raw-LZ4 records independently compared against liblz4. XML signatures and CRC algorithms were not verified; package provenance is not an authenticity claim.

Main runtime SHA256: `50130235f52573cc9facda89795486387ac4eb73a999026983694fd91d379761`.
Main process virtual addresses equal file offsets + `0x10000`. Physical NOR destination `0x49800000` is not that virtual base. All offsets below refer to this older image only; none is an address to patch on the installed vehicle.

## Why the existing PiP sender does not reach the windshield

Twelve executions of actual receiver Thumb code establish:

| Contract | Executed result |
|---|---|
| B009 sender, requested selection 0 | Aspect 1.0, **277×160**, HUD selection 0 |
| B009 sender, requested selection 1 | Aspect 1.0, **460×237**, cluster selection 1 |
| Metadata byte 4 = 0 | Internal destination 1 / HUD |
| Metadata byte 4 = 1 | Internal destination 2 / cluster |
| Metadata destination differs from receiver destination | **No PIP_UPDATE event** |
| Metadata destination matches receiver destination | PIP_UPDATE event `0x2ae` |

The complete metadata callback at file `0x2a6a9c` was executed, including its real frame-ID and destination gates. External event-store access, logging, memset and final event delivery are explicitly intercepted; this is not hardware simulation. Frame IDs must differ from the last ID for that slot; the code does not require an exact increment of one.

Local event `0x1eb`, payload 1, invokes `requestDisplaySink(0)` and sets expected HUD destination 1. Payload 2 requests cluster selection 1 and sets expected destination 2. This is one coupled receiver operation through a real vtable/thunk, not two independent inferred flags. The upstream generated state-machine policy is the remaining activation trace. A registration involving source data event `0x292` and state-machine event `0x1eb` uses a different event namespace and must not be conflated with the desired-sink data event merely because the numbers match.

This explains a concrete failure mechanism consistent with our live observations: the receiver negotiated cluster selection 1, while our producer supplied HUD metadata. Changing metadata alone cannot change that receiver gate. Do not forge a selection-0 acknowledgment in response to selection 1.

## Where the narrow-strip boundaries come from

The actual road renderer checks cumulative width, per-entry spacing, resource kind, and image height. Its initializer copies dimensions from the bound `GS2RoadName` / `GS3RoadName` objects into widget bounds. Native instruction execution confirms this bound-object-to-viewport copy without intercepted instructions; supplied dimensions in that check are synthetic, not measured scene dimensions.

Thus increasing B006 bitmap capacity or rearranging image entries does not itself enlarge the receiver scene widget. The full scene geometry and PiP visibility policy must be traced separately.

## PiP scene visibility and ownership

Five additional native executions of `PiPNavi` arbitration (process VA `0x28e576`) establish a separate render gate: a hidden node or hidden ancestor prevents this widget from updating. A different currently visible PiP owner retains ownership. Once that old owner is hidden, the candidate can take ownership and proceed to downstream rendering. The parent walk is executed at `0x28e5b6`; synthetic objects supply visibility bytes at node `+0xb8` and parent links at `+0xe4`. Downstream renderer calls are intercepted and recorded, so these checks prove arbitration, not pixel output.

Consequently, genuine HUD sink negotiation alone is insufficient: the correct windshield scene must also be visible and own the PiP renderer. A test that only changes metadata or fabricates an acknowledgment cannot demonstrate this.

The decoded `hud_2d` asset contains factory test-bitmap records with serialized 408×132 values and height-frame corners. These are asset fields, not an exposed custom-image API. Its RoadName leaf records contain 1×1 values; they must not be confused with the bound runtime RoadName objects used by the road renderer. The visibility helper dereferences the object's node pointer at `+0xc`, while the width/height copy reads the object itself at `+0x3c/+0x40`. Exact property binding remains to be decoded.

## Receiver image fitting and actual failed-ruler decode

A further14 native cases execute the receiver itself: six image-fit cases and eight RLE decoding cases, including the exact36×36 ruler request that failed visually on19November. All expected pixels match the receiver decoder output. The decoder at processVA `0x2d303c` only has its allocator intercepted. This supersedes the earlier head-unit-only decoder evidence for this older receiver version; it does not establish installed008 compatibility or visible attachment.

The HUD list external-image path at `0x246672` reads the target node's Candera Rectangle dynamic property through ARM getter `0x1213d0`, takes its width/height at property offsets `+8/+0xc`, looks up the cached image at `0x2b21fe`, and invokes `0x25740c`. That function uploads the image and calls the fitter. At `0x257060`, native code computes `min(1, target_width/image_width, target_height/image_height)` and applies uniform scaling. A277×160 image with a150×36 bound rectangle becomes62.325×36; with a277×160 rectangle it retains full size. These rectangles are synthetic inputs, not measured installed widget geometry. The vector constructor and final renderer scale setter are intercepted; the scale decisions execute natively.

The `CopyBitmapImage` diagnostic “Image dimension mismatch” at `0x2afef4` checks whether the dimension-vector count is2. It is not itself a width/height clipping comparison. The cache insertion at `0x2b1ab0` separately limits encoded payload length to `0x14000` bytes and stores source dimensions. Enlarging that payload capacity would not enlarge the target rectangle.

The receiver row-copy path at `0x2b0536` routes columns0/4 through bitmap copying and columns1/2/3 through text copying. This supplies receiver-side context for the failed Entertainment text substitutions. It does not explain away the separately failed Carousel icon replacement, and is not admission for another menu test.

Private native checks of high-guidance availability additionally execute `0x2b54b2`: detailed types3/7/10/13/49 read picture references at offsets0x10/0x38/0x14/0x70/0x14 respectively. Presence means reference≠0xffffffff; it does not validate the referenced image or select a display. Twelve synthetic cases pass. These are receiving in-memory offsets, not wire offsets and not a newly admitted branch/tunnel test.

## Larger renderer evidence

The older receiver's production HUD initializer at file `0xfde1c` selects display index 1, enables warping, and configures **480×240, 18-bit** output. Executed arguments also contain a refresh configuration; no refresh-rate car test was performed or proposed. This production path is not proof of an accessible arbitrary-image API, and its dimensions are not automatically those of installed version 008.

A separate `imgviewHUD` handler uses predefined asset lookup and a HUD window. Its existence does not establish a reachable Ethernet command or permission to run production tests on the car.

## Reproduce offline

Supply the private decoded image; no OEM binary is distributed in Git:

```sh
python tools/verify_receiver_sink_native.py --image /absolute/path/5ffc-49800000.bin --output /absolute/path/receiver-verification.json
```

The separate visibility verifier uses the same arguments:

```sh
python tools/verify_receiver_pip_visibility.py --image /absolute/path/5ffc-49800000.bin --output /absolute/path/pip-visibility.json
```

The image decoder/geometry verifier also accepts an optional private captured failed-ruler request:

```sh
python tools/verify_receiver_image_geometry.py --image /absolute/path/5ffc-49800000.bin --output /absolute/path/image-geometry.json --request /absolute/path/012-request.bin
```

Requires Unicorn. The verifier rejects any image whose SHA256 differs before using offsets. It has no network or vehicle operations.

## Next test admission

A new larger-windshield test must identify the receiver policy transition that requests HUD selection 0, preserve its genuine handshake, and withdraw the owned image and graph cleanly. The candidate must prove custom pixels beyond the 36-pixel-high road strip. Another flag, distance, alignment, or narrow-strip permutation is not admitted on this evidence alone.

V1 installation remains unchanged. The owner deferred restoring its runtime at the latest session end. Do not describe it as reinstalled, currently running, or modified by this offline analysis.
