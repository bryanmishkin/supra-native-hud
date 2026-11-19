# Pixel binding and executable geometry tests

This revision uses the captured HmiMain3D binary and existing factory model bodies. No firmware purchase, vehicle connection, V1 modification, or Hz test is involved. It prepares a bounded test of larger **widget-backed image areas**; it does not claim arbitrary access to the root windshield framebuffer.

## Image data, not just matching field names

Binary SHA-256: `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`.

The provider getter at `0x2594db8` checks content type8; its assertion string explicitly says `ContentTypeRLE32Image == m_eContentDataType`. At `0x2594e08..0x2594e20` it copies the two halfword dimensions from provider offsets `0x2c/0x2e` and copies the image data from `+0x30` into the returned image structure. This establishes the type8 content's actual representation as RLE32, not a generic bitmap assumption.

The allocator at `0x2593194..0x2593234` rejects zero width/height and dimensions above the configuration, selects a bitmap resource ID, preserves both dimensions and calls `setRICBitmapResource`. That sender at `0x2592b44` checks dimensions again, constructs resource type1, a dimension vector and image data, then submits the resource at `0x2592d00`. It does not turn this image into a preinstalled icon selector.

The earlier caller trace then places the returned resource ID into Carousel content word1/2 (zero-based) or an Entertainment content cell. The separate icon field was the wrong producer path to use as evidence of bitmap support. The failed square-only experiment still does not prove that changing fields alone will render on the Supra receiver.

## Executed factory dimension branch

`tools/verify_b00e_pixel_path.py` runs the actual captured ARM instruction block in Unicorn, hash-gated to the binary above. Seven in-bounds shapes reach the resource submission boundary with their dimensions unchanged: 36×36,64×64,96×96,128×128,128×36,128×64,64×128. Zero and129-pixel dimensions take the rejection branch. The resource ID is preserved as `0x01000009` in the exercised pool state.

Explicit boundaries: the configuration helper supplies the measured128×128 limit; the C++ vector-copy helper is skipped; the sender's arguments are observed, not transmitted or executed. This proves the producer branch and rectangular dimension handling only. It is not a simulated receiver or a visible canvas result.

## Geometry test implementation

The executable B00E runner now accepts explicit width/height, while preserving legacy square `--size` use. The named-case launcher validates the image hash and exact allowed dimensions. No new resource range, model type, display selector, or oversized upload is introduced.

`canvas_geometry.py` creates opaque asymmetric rulers:

- Cyan top, orange bottom, green left, magenta right.
- Eight-source-pixel ticks, a central cross and unequal corner marks.
- Wide/tall pairs that expose aspect-ratio changes and clipping.

The generated kit contains60 available cases across the two traced content fields in Carousel and Entertainment. **This is an option matrix, not60 mandatory runs.** All use30-second observation windows after posting; no throughput tests.

### Minimal discriminating session

1. Capture current complete Carousel and Entertainment snapshots and validate current admission; preserve installed V1 and pause it cleanly.
2. Try36×36 ruler in Carousel content1, then content2 only if needed. If neither shows distinct pixels, try Entertainment columns1/2 on a visibly identified row. A generic factory frame is a failure to demonstrate image binding, not success.
3. For each genuinely working placement, test128×36 followed by128×128. If clipping occurs, use128×64 or96×96 to bound it. Use64×128 only to distinguish scaling/aspect behavior. Stop escalation on rejection or uncertain cleanup.
4. At the largest unclipped placement, show the IU fixture. Record windshield and cluster separately, alongside factory speed/limit references.
5. Withdraw focus, restore the exact current factory body, commit, remove only our resource and verify absence after every case. Restore and verify the unchanged V1 afterward.

The existing runner performs the restoration/removal sequence. A positive acknowledgment does not count as visible success. Operator observations and original camera evidence remain separate from protocol results.

## Main-surface leads examined in the same pass

Additional exported HMI proxy vtables were followed to their concrete dispatchers rather than classified by name:

| Interface | Dispatcher | Observed payload handling |
|---|---|---|
| HUD_Terminal AdjustHUD | `0x22e924c` | Three scalar byte reads, each bounded0..255; stored as settings/status fields |
| HUD_Terminal HUDSelection | `0x22e9634` | A scalar field read, stored at object+0x78; neighboring sender compares a halfword |
| KombiExternalDisplay | `0x230160c` | Three bounded16-bit fields (65535,4095,4095 maxima), then byte enum0..3; no image array in this dispatcher |
| Nav_KombiResolutionChange | `0x2357a48` | One byte0..1 delivered to registered callbacks; not a width/height or pixel payload |

These results prevent treating promising names as additional canvases. The two4095-bounded fields are not labeled width/height without a traced consumer. They also do not disprove a downstream drawing interface. The captured main-root implementation and arbitrary-coordinate drawing contract remain unresolved; no root sender is fabricated here.

Private evidence bundle: `hud-surface-audit-2026-11-19`, containing bounded disassembly, factory-block execution output, hashed image kit and source snapshot. No OEM binary bytes are committed to Git.
