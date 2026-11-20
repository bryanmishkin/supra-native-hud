# Windshield boundary trace and right-alignment experiment

V1 is unchanged. This work is offline. It does not establish access to the whole HUD compositor or a larger usable height. The next experiment is a placement/clipping contrast, not a promise of an expanded viewport.

## What actually defines each known extent

| Layer | Evidence | What it controls |
| --- | --- | --- |
| Bitmap resource | Receiver B006 create response and native model configuration setter `0xa25db8` | Maximum individual road icon size 150 × 36; not a declared viewport rectangle |
| Road-list model | Native writer `0xbbcd70` and exact accepted model40 packets | Road type, list alignment, nested image references and per-entry fields; no x/y/width/height/clip rectangle |
| Producer alignment | Native diagnostic branch `0xa47434..0xa47450` | Alignment 0 is **Left**, 1 is **Right**. Actual ARM execution selects these labels without intercepted calls |
| Receiver arrangement | Owner observations and photographs | Separate entries render side-by-side in windshield; two images in one entry did not. Second separate-entry image was truncated |
| Receiver clipping / optics | No captured receiver rasterizer and no controlled eye-position comparison | Which component sets the observed right cutoff is still unknown |
| Navigation style definitions | Captured NavigationFully XPDs, previously native-verified | Producer render-element geometry for navigation/PiP. No evidence these definitions set the model40 road-list windshield clip rectangle |

The new label trace is in the captured controller SHA-256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`. Alignment is loaded from source object +0x25; zero selects string `Left` at `0x103ea68`, nonzero selects `Right` at `0x103eaa8`. Only supported enum values 0 and 1 are admitted. This names a layout control, not its receiver implementation.

`verify_road_list_native_wire.py` now executes eight native serialization cases: empty, single image, two images in one entry, and separate entries, each at alignment 0 and 1. Exact output matches the codec. Native serialization DTO alignment is the u32 at +0x0c; it is not the source-model byte offset. This distinction was verified rather than assumed.

## New test: right_boundary_ruler

The accepted separate-entry graph changes exactly one layout field: alignment 0 → 1. All other setup model fields and all seven withdrawal commands remain byte-identical. Two owned 150 × 36 bitmap slots carry static asymmetric rulers instead of numbered images. No Hz tests, no previous control repeats, no new resource slots, no shared-instance disposal, no persistent V1 writes.

The source ruler consists of two 150-column tiles. Cyan marks the first tile's left edge, magenta marks the tile seam, green marks the second tile's right edge. White ticks are 10 source pixels apart; orange ticks are 50 apart. The first tile has an upper cyan interior line; the second has a lower orange line. **These source coordinates are not claimed as contiguous screen coordinates:** the receiver can insert gaps, reverse order, overlap, scale or clip.

The full 30-second window asks whether Right changes the projected footprint or which edge is clipped. Record the windshield and cluster separately. First record from the normal viewing position; while parked, a small camera-position change can distinguish an optical cutoff that moves/reveals pixels from a cutoff that remains fixed in the graphic. Do not adjust HUD height or factory settings.

Success toward the larger-area goal requires a visible footprint extending beyond the documented single-image/V1 footprint, with identifiable edges/ticks. Merely seeing the ruler, an ACK, or the green edge is not sufficient. A narrower/differently clipped footprint is an informative placement result, not expansion. Do not infer a 300-pixel canvas from the combined source width.

If this selector is ignored or only rearranges content within the same clip, do not repeat it or cycle unrelated enums. It does not answer the full-height/main-canvas question. That requires a receiver layout control or a separately demonstrated render target; neither has been identified by this trace.

## Executable batch and gates

Use `manage_road_list_session.py prepare --boundary-only` with the retained create response and accepted profile. This creates a batch containing **only right_boundary_ruler**. Current private kit: `outputs/hud-viewport-boundary-2026-11-20/session-kit` in the workspace. Historical kits pin older source and must not be reused.

1. Obtain current diagnostic access and confirm parked/normal displays, updating V1 and closed navigation/radio.
2. Run manager `pause --execute` with the existing verified SSH socket. It reads and verifies all 15 installed V1 files, cooperatively stops V1, and checks quiet state. A missing resident.status now causes a cooperative stop attempt rather than a failed read or an assumption that the app is stopped.
3. After visual clearance, run manager `case --case right_boundary_ruler --execute --displays-clear --guidance-closed`. Tell the owner **WATCH NOW** at the actual window start. The runner journals requests/replies and checks image existence throughout.
4. Record the observed edges, clipping and positions in manager `observe`, including separate display counts and visual clearance. Ambiguous/failed cleanup blocks completion.
5. Restore V1 through the established normal restart. Run manager `finalize --execute --v1-visible` only after owner confirms updating V1. Require 15-file readback, advancing frames/samples/heartbeat, healthy supervisor, enabled/no lockout, empty secondary output before declaring machine-verified restoration.

Offline transport failure checks include this new case: lost replies at every request position, both occupied image slots, interruption and recording failure. These exercise the real trial/session code but do not simulate physical receiver layout.

## Readiness distinction

The bounded right-alignment experiment is implemented and offline-tested. A guaranteed drawing test beyond V1's physical area is **not** established, nor has the actual receiver viewport rectangle been located. Do not describe this as an unlocked larger canvas or ask for a car trip on that premise.
