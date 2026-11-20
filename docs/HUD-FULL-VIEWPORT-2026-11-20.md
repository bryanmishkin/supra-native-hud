# Full viewport investigation after the destination/narrow-tail session

Offline only. No vehicle connection, V1 code/startup change, or installation. The owner explicitly deferred V1 runtime restoration at the last session; installed files were preserved, but runtime restoration must not be claimed.

## Photo evidence reconciled with the live records

| Originals preserved privately | Visible result | What this establishes |
| --- | --- | --- |
| IMG_2001.JPG | Cluster cyan boxed 1; factory finish flag and 400 ft below | Reference bitmap plus factory destination graphics |
| IMG_2002.JPG, IMG_2003.JPG | Same composition in windshield | Destination layout reaches windshield; custom destination cross was not observed |
| IMG_2005.JPG, IMG_2006.JPG | Cyan ruler/bar and separate amber panel with all three white marks and green far-right rail | Complete narrow tail on windshield; both panels retain the strip's height |

The owner separately confirmed narrow-tail visibility on both displays. These five photos do not include a cluster narrow-tail close-up. Do not present them as one.

Correct the watch-prompt record: the narrow-tail reference was a ruler/bar, not a cyan numeral 1. Its source images were 150×36 and 64×36. Their summed width is not a demonstrated contiguous 214-pixel framebuffer: the receiver supplies spacing, scale and layout. No new vertical drawing extent or root canvas has been established. The destination flag/distance below the bitmap are factory graphics, not custom pixels outside the strip.

The earlier full-width second image was clipped on the HUD while complete on the cluster. The new complete narrower image does not identify whether the earlier cut was receiver clipping, layout or optical visibility. It also does not establish the maximum width.

## Newly executed adjustment and mode contract

`tools/verify_hud_adjustment_contract.py` executes captured HmiMain3D ARM code, pinned to SHA256 `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`. This is not a receiver emulator.

- `CDevCarHUD::setMode` at `0xf4a6c0` compares the requested mode with object+0x8c. An unchanged mode sends nothing. Otherwise it calls `0x230774c` on proxy parent+0x25f4.
- The sender receives nine values: `[0,6,0,mode,0,0x40000000,255,255,255]`. The native serializer bounds these respectively to `[31,7,31,7,31,0xffffffff,255,255,255]`; only the sixth value uses the 32-bit scalar writer.
- Three adjustment methods at `0xf4a720`, `0xf4a788`, `0xf4a7f0` accept signed −10..10 and encode input+11 in different fields of the same message. They reject −11 and +11 without sending. This is not arbitrary x/y/width/height geometry.
- Status consumer `0xf4b440..0xf4b538` accepts adjustment codes 1..21, subtracts11, and updates object fields+0x80/+0x84/+0x88. The mode consumer at `0xf4b5ec..0xf4b638` accepts values through3 and updates object+0x8c. The serializer's wider bound does not prove other values are useful modes.
- A distinct adapter, `CDevCarHUDRueKo`, explicitly rejects setMode at `0xf4b81c`. Its two-byte adjustment path is documented in [the prior control trace](MAIN-HUD-CONTROL-TRACE.md). Do not conflate the adapters or choose a live mode from the native range alone.

The verifier passes13 caller/serializer cases, four unchanged-mode cases, and six rejected adjustment cases. Initialization, scalar writers, cache invalidation, transport submission and destruction are intercepted and disclosed. The actual method logic executes; the receiver and physical display do not.

The two retained CA6 SET bodies, `00060a060040000000ffffff` and `00060b060040000000ffffff`, match the nine scalar values produced by `0xf4a788` for UI−1 and UI0 exactly. This ties the captured adjustment traffic to the native caller. It does **not** tie the full-frame corner graphic's pixel generation to that call. Neither saved body is the separate setMode call.

Reproduce with the private original binary and the existing analysis environment containing Unicorn and pyelftools:

```sh
python3 tools/verify_hud_adjustment_contract.py /absolute/private/HmiMain3D
```

## Actual next larger-canvas test status

**Not admitted yet.** Destination-picture and narrow-tail are completed experiments, not a pending larger-canvas batch. No Hz, alignment, menu-text replacement or same-strip repeat is requested.

The unresolved attachment is between receiver-owned layout/clip and a custom image surface. Local MapCanvas bounds are proven but not linked to windshield output; PiP custom pixels are proven on the cluster but the recorded selection remains1. The full-HUD corner outline proves factory rendering exists there, not that its interior accepts client pixels.

A useful next test must supply a traced windshield-bound image target or actual receiver clip setter, exact withdrawal/inverse operation, and a marker visibly above/below the strip as well as a retained strip reference. Changing image arrangement or displaying a factory symbol below it does not qualify. No live command or binary is produced from an unproven mode enum.

Continue from the receiver's layout/clip implementation or a destination-bound image attachment, using the [capability map](HUD-CAPABILITY-MAP.md) and [batch admission contract](HUD-NEXT-CANVAS-BATCH.md). Do not infer a framebuffer API from the height controls. Private evidence includes original photos and hashes, native disassembly, executable adjustment results and packet-to-scalar comparisons.
