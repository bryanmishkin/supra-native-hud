# Main HUD control path — 2026-11-19

Offline analysis of captured HmiMain3D SHA-256 `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`. No vehicle commands or V1 changes.

## Concrete control chain

`CDevCarHUDRueKo` is identified by RTTI at `0x2e8e76c`, naming string `0x2e8e758`, and adjacent source path `libmyvvehicleconfig/source/CDevCarHUDRueKo.cpp`. Its vtable begins `0x2e8e6a0`; entries at `0x2e8e6d4` and `0x2e8e6dc` point to setters `0xf4bbcc` and `0xf4bb70`.

Both setters reject values outside signed −10..10. Their 21-entry conversion table starts `0x2e8e570` (12 bytes per row). Each row contains the signed UI value, a word representation for the alternate proxy, and a byte representation for HUD2. Conversion values from −10 through +10 are `254,235,223,211,199,187,175,163,151,139,0,12,24,36,48,60,72,84,98,108,127`. These are adjustment codes, not demonstrated pixel positions or dimensions.

When object flag `+0x9f` is set, `0xf4bbcc` changes the first byte and `0xf4bb70` changes the second. Both tail-call `0xf4b994`, passing `0xff` for the unchanged byte. That helper replaces `0xff` with current status via `0x22ea3b4` (first) or `0x22ea378` (second), from proxy child `+0x730`. It calls `0x22ea1a8` on child `+0x6c4` at `0xf4b9f4`.

`0x22ea1a8` initializes a command, appends two scalar values with bounds 0..255 through `0x2195efc`, then submits with `0x2191e40`. There is no image byte array, bitmap ID, framebuffer pointer, stride, width, or height argument in this traced chain. This is the `CControlHUD2` control path. The two exact UI labels have not yet been established; calling them height and brightness merely from their ranges would overstate evidence.

When `+0x9f` is clear, the setters instead tail-call `0xf4ba00`, passing the corresponding table word and `0xff` sentinels. This is a distinct legacy/alternate proxy path, not evidence of a second drawable canvas.

## What this changes

The head unit exposes explicit root-HUD adjustment controls in addition to B00E content models. Their presence does not grant ownership of the complete windshield framebuffer. Existing constructor evidence maps children to registrations `0x410/0x411/0x415`; these must not be reused as guessed live MOST function IDs.

The status-preserving sentinel behavior matters: raw values of `0xff` are resolved by the device adapter before submission, so replaying arbitrary values into the proxy could change settings rather than request a blank image. No live exploration of these controls is prepared or recommended by this trace.

Private reproducible evidence: `outputs/main-hud-renderer-trace-2026-11-19/control-path/`, including exact caller disassembly, setter wrappers, conversion table, and direct-call scan. Direct BL searches found one caller of `0x22ea1a8`; absence of other direct callers does not exclude virtual or tail calls.
