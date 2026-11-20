# Receiver scene bounds and test-surface control

Offline evidence only, using Toyota J29 SWFL 00005ffc 004_000_003. The installed receiver is 008_000_000: these addresses and defaults are not permission to patch it. V1 files and vehicle state were not changed. Owner deferred runtime restoration during the previous car session.

## Road strip: named bounds, not inferred pixel limits

`tools/decode_receiver_widget_properties.py` decodes the scene's widget property records. A property string pointer includes the 12-byte outer record header: subtract 12 before indexing the decompressed payload. The HUD 2D scene has 58 widget records.

Both `hud_2d_Widget_NaviComingRoad_GS2_RoadName` (record 0x24ba4) and GS3 (0x24d6c) are `HmiLabelFading2D` with Width 230, Height 36, baseline 27 and fading width 50. The `NaviComingRoadHud` widget explicitly binds them. These are runtime label defaults; the raw road leaf's 1×1 values were not its runtime label bounds. Icon-text labels are 230×33.

A private native replay supplies the decoded 230/36 values to width setter 0x20e918 and height setter 0x20e94a, then executes the initializer at 0x266fde..0x267022. It obtains both cached bounds `[230,36]`. No instructions were substituted. The complete scene loader was not executed.

## Visibility is tied to named destinations

The six guidance-policy replays in `tools/verify_receiver_guidance_policy.py` execute the actual state engine and transition data with synthetic starting states. They run 0x2a7676, 0x2a7696 and 0x2a78dc without instruction substitution. Returned render actions are recorded, not executed. The decoded table has 10,008 transitions.

In the tested GS3 states, Kombi metadata selects the show action; HUD/NotSet metadata selects hide. APIX uses PiP show/hide; OABR uses CCP show/hide. The action is not an arbitrary destination switch.

Visibility setter 0x1a56ac stores a boolean and dirty flag in a 12-byte entry at 0x2043dfc. The name table at 0xc702dc resolves index 0x67 to **ki_NaviPiP** and index 0x25 to **ki_2d_NaviHgCcp**. The binding loops 0x1a2e42 and 0x1a46xx resolve names against the scene graph. Thus the traced PiP visibility action controls a cluster node. It does not establish a windshield PiP attachment or write desired-sink data event 0x1eb.

The separate HUD 3D scene has five widgets. Its carousel uses factory active/inactive icon atlases with `currentIcon` shader selection. The HUD 2D carousel label is not proof of an externally uploaded 3D icon binding. No PiP-named node was found in these two decoded HUD scenes; this is not a claim about every firmware or dynamically created node.

## Separate windshield test surface: 408 × 132

The HUD scene binds `TestBmpHUD` to `hud_TestBmp`, with separate `hud_TestBmp_Bmp` and `hud_TestBmp_SolidColor` nodes. Their serialized bounds are **408×132**, at scene record offsets 0x658 and 0x6f0. Visibility-table index 0x20 resolves to `hud_TestBmp`.

Native control contract:

- Widget initialization 0x296b88 subscribes to local data event **0xac**.
- Callback 0x296baa and copier 0x296bce consume five bytes: selector, red, green, blue, enable. The copier also marks the widget dirty.
- Update 0x296be8 requires enable=1 and selector<128. Selector 0 sets a solid brush from RGB/255; it does not use an uploaded image.
- Nonzero selectors resolve through 0x296edc and the 25-entry table at 0xc75920, initialized at 0x296efc. The table contains factory full-surface colors, grids, ghosting, distortion and alignment patterns. An unknown selector falls back to factory selector 0x60.
- Disable branch 0x296ec0 clears both render nodes' visibility flags at node+0x36. It does not resize the road widget or replace V1 resources.

`tools/verify_receiver_test_surface.py` executes initialization of this asset lookup, all 256 byte selector inputs, the five-byte record copy, and the disable slice. All pass without substituted instructions. It checks both scene bounds and pins all three input hashes. Full brush rendering is not emulated. Selector 0 has a table entry but the update's solid-color branch bypasses that lookup.

## Traced input path, verified in native execution

Internal receive-record **0x16e** has a five-byte value and a sixth status byte. Table 0x48f098, entry 0x4912e8, supplies decoder 0x140e5c. The exact chain is:

`0x14267c → 0x140e5c → 0x142314 (group 0x31, field 0) → 0x149f30 → 0x3fc40a (external 0xe0 → local 0xac) → 0x190cd2`.

`tools/verify_receiver_test_surface_input.py` executes that chain using `[0,17,34,51,1,1]`. It reaches event enqueue with local event 0xac and unchanged payload `[0,17,34,51,1]`, with no instruction substitution. Execution stops before enqueue. Required enable/mode memory and the receive record are synthetic. This proves internal argument flow, not network reachability.

Upstream, 0x13bc4c dispatches records with a seven-byte `BA BE` header. Header creation is at 0x13ba20. The parser 0x13bc8a is module 0x14's callback in table 0x489a04; the enclosing input parser 0x13939a receives 64-byte frames with a checksum check at 0x138f8a. This path reaches low-level device handle initialization at 0x1390fe and transfer routines 0x13b06a/0x13a78e. **No Ethernet address/port or diagnostic request has been established for it. Do not transmit these internal records over ENET by guessing an endpoint.**

## Historical admission status before auxiliary tracing

The useful new finding is an actual larger windshield-bound surface and its internal control contract. Arbitrary custom bitmap attachment, externally reachable activation, parent visibility restoration and compatibility with installed 008 remain unproved. A factory pattern or full-area RGB fill alone does not satisfy the requested larger custom canvas. No repeat strip/Hz test or speculative live runner was added.

Reproduce the four public tools with `--help`; receiver binaries and scene inputs remain in the private evidence archive. Reports distinguish actual native execution, synthetic setup, decoded assets, and visual observations. See [the next canvas admission contract](HUD-NEXT-CANVAS-BATCH.md).

## External diagnostic activation resolved subsequently

The [A102 diagnostic trace and prepared tests](HUD-DIAGNOSTIC-SURFACE-TEST-2026-11-20.md) now establish the external routine registration, native request parser, asynchronous descriptor and five-byte writer in the auxiliary component. The earlier lack of an endpoint is superseded by that evidence. Two bounded full-surface activation tests are prepared. Arbitrary uploaded-image attachment and installed008 behavior remain separate, unverified questions. The renderer verifier now follows enable2 into the disable branch, rather than entering the disable slice directly.
