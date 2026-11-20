# B00E bitmap-producing content cells

> Superseded test readiness: the second/third Carousel fields and Entertainment content fields described below were subsequently tested and did not show custom pixels. See CANVAS-BINDING-LIVE-2026-11-19.md and HUD-BINDING-CAUSAL-REVIEW-2026-11-20.md. Preserve the producer trace, but do not repeat these as untested candidates.

Offline firmware trace, 19 November 2026. V1 unchanged. This follows the square-only Carousel experiment and the successful exact factory-content control. It establishes a different producer-to-field path; receiver acceptance and visible image placement still require proof.

Captured HmiMain3D SHA-256: `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`.

## What the photographs establish

The owner reported a square for both 36×36 cross and IU variants. Actual sent packets decode to distinct correct pixels, and cleanup succeeded. The supplied photograph IMG_1962 shows a broad rounded rectangular outline with an empty interior, unlike the sharp square border/cross and IU fixtures. Together with the successful factory-content control, this supports a factory widget/container explanation. It does not prove an alpha-mask problem, a bitmap decoder failure, or a larger custom pixel canvas. The parent session audit associates photographs with exact runs.

## The field distinction matters

CarouselElement serializes four resource-sized words. Historical observed elements mostly use:

1. Preinstalled icon reference.
2. Text/content reference.
3. Text/content reference.
4. An absent reference in the traced paths.

Calling fields 2 and 3 **text-only** is incorrect. Their factory producer can return bitmap resources.

### Shared content allocator

Function `0x2592e3c` obtains table cell content through provider virtual offset `+0x18` at `0x2592ebc` / `0x2592ec0`, passing row and column. It obtains the result's data type through `0x25945b0` and branches:

- Types 1 and 2 take the text-resource branch at `0x2592eec`.
- Exactly type 8 takes the bitmap branch at `0x2593150` (comparison `0x2592ee0`, branch `0x2592ee8`).
- Other types return the absent/error path.

The type-8 branch reads bitmap data through `0x2594db8`, checks nonzero and configured maximum dimensions, selects an ID from the bitmap pool, calls `setRICBitmapResource` at `0x2593230` → `0x2592b44`, and returns that ID through the common exit. The sibling text path and bitmap path therefore produce different resource types through the **same return value**.

### Carousel: actual bitmap producer flows to fields 2 and 3

The direct caller scan finds three ARM BL sites to the allocator. Two are in `CPeerICList::updateRICCarousellist`:

| Call | Provider cell | Returned ID storage | Serialized Carousel field |
| --- | --- | --- | --- |
| `0x2586134` | Current row, column 0 | fp−0x50 then element+8 at `0x258618c` | Second word |
| `0x2586154` | Current row, column 1 | fp−0x4c then element+0xc at `0x2586194` | Third word |

Column 0 is set at `0x258612c`; column 1 at `0x258614c`. The separate first-word icon path does not call this allocator. This distinguishes the failed first-icon-field substitution from the factory's actual bitmap-producing content-cell path.

The element serializer at `0x292008c` emits the four words in order. No type coercion to text occurs between the allocator's returned bitmap ID and the second/third word stores. This is evidence for a real alternate content binding, rather than guessing another display selector.

### Entertainment: resource-bearing list cell

The third allocator call is `0x2587774` in `CPeerICList::updateRICEntertainmentlist`. Its returned ID is stored at ListElement+4 at `0x258777c`. The first list column is populated separately from the provider's icon getter (`virtual +0x34`, call `0x2587830`, store `0x2587834`); subsequent cells use the content allocator. ListElement's serializer `0x292155c` emits its resource word and state field.

Thus the Entertainment table has a concrete image-producing content-cell route too. This is not proof that its receiver reserves unrestricted bitmap area or permits an arbitrary fullscreen surface.

## Next bounded candidate justified by this trace

Use a **complete current factory Carousel snapshot**, preserving its four-element layout, focus index, trailing flags and all other references. Replace exactly one selected element's second content word with the tracked custom bitmap; restore the exact snapshot before deleting that bitmap. A separately labeled third-word case can test the second content column if needed. Preserve the known factory icon and the other content word so the container remains comparable.

Do not describe this as already working, an independent session, or a guaranteed larger surface. The static path is proven on the HU producer, while the Supra receiver's visible result is still unverified. Start with a distinctive small marker, observe windshield and cluster separately, and require visible removal plus protocol/resource cleanup before any size increase. An exact-snapshot first-icon-field control may still isolate the earlier one-element/all-text-absent test's layout confound, but it is distinct from the producer-backed content-cell candidate.

Private evidence: `b00e-binding-tests-2026-11-19/canvas-followup/resource-calls.json`, `allocator-cells.json`, `ent-builder.json`, `ent-provider-setup.json`, and the retained Carousel model-builder disassembly in `removal-agent`. No vehicle connection or software modification was made for this trace.


## Canvas and model inventory after this trace

A model is a factory-rendered widget. An advertised bitmap limit is a resource limit. Neither automatically grants a free-positioned canvas.

| Path/model | Present evidence | Custom-pixel status | Next readiness |
| --- | --- | --- | --- |
| B006 guidance road icon | Installed V1, 150×36; control images visible; cleanup verified | Working known surface on reference vehicle | Existing bounded runner and restoration procedure |
| B00E Carousel 0x6d/type0x1c | Advertised shared dimension 128×128; four entries; actual factory source icons/text visible | First-icon replacement with a one-item model showed only an empty frame; content-cell replacement not tested | Producer-backed second/third resource-word candidates; exact-current-snapshot preservation required |
| B00E Entertainment 0x66/type0x16 | Actual station-list models; content allocator can return a bitmap into ListElement.resource | No custom-image result | Exact Entertainment codec now verified against 180 captured bodies; current full snapshot and separately admitted runner required |
| B00E Voice 0x6e/type0x2f | Wrapper around Carousel state/config; captured factory voice transitions | No custom-image result; inherited advertised dimensions are zero | Wrapper relationship alone does not establish a useful image area; no executable drawing candidate |
| B00E UnifiedCall 0x68/type0x2d and IncomingCall 0x67/type0x17 | Advertised models; UnifiedCall captured | No traced custom bitmap-producing caller to these model fields in this work | Need producer-to-field path and separate full snapshot/cleanup codec |
| B00E Notification 0x69/type0x19, Popup 0x6a/type0x1a, RadioTune 0x6b/type0x30 | Advertised model types and fixed factory ID map | No demonstrated custom bitmap binding | Configuration availability is insufficient; no executable candidate |
| B00E Coverflow | HMI CommonTypes structure exists | No matching config advertised in the retained B00E create reply | Do not select solely because firmware contains its type |
| B00E PiP / generic local HMI textures | HMI symbols and prior transport traces exist | No working windshield pixel binding; prior arrow-only trials failed | No PiP config variant in current B00E reply; retired trial must not be relabeled fixed |
| B011 check-control assets | Cluster-to-HU retrieval of factory PNGs including door graphic | Downloaded assets, not an upload canvas | No custom-drawing candidate |
| Factory speed/speed-limit region | Visibly distinct factory HUD content | No arbitrary-image producer established | Not an acquired custom canvas |

The bounded square bitmap resource ceiling is128×128 for the retained B00E profile. The factory Carousel dimension type is confirmed by shared RicDimension vtable construction, while actual visible extent, scaling, clipping, and content-cell layout are still receiver measurements. No position/origin coordinates were found in the CarouselElement's four-resource-reference serializer.

### Entertainment codec now prepared

`tools/b00e_entertainment.py` now decodes and re-encodes the exact Entertainment envelope and nested table. All **180 retained captured bodies** replayed byte-identically. The retained bodies contain 11, 21 or 30 transmitted rows, each with five columns. Nine unit tests cover exact round trip, a replacement confined to one four-byte resource field, invalid lengths/identity/variant, bounds, icon-column rejection and absent-ID rejection.

The generic native model serializer at `0x29260e4` writes a nested prefix, six 16-bit metadata values, a 32-bit header reference, a length-prefixed array of length-prefixed rows, and four trailing 32-bit references. `ListElement` serializer `0x292155c` writes a resource word and one-byte state. The body variant is type `0x16`, tag 3, factory model `0x66`, shared handle 100.

`replace_content_cell(body, resource_id, row_index, column_index)` preserves every other byte. Row index is explicitly relative to the transmitted array; it is **not** inferred from the six metadata fields, whose individual semantic names remain unproven here. Column zero is the separate icon and rejected; columns 1 onward follow the content allocator. This is a codec and mutation primitive, not a live sender or proof the receiver shows custom images.

A live candidate still requires a full current-session Entertainment model snapshot, admission, a specific existing content cell, original-byte restoration, independent image allocation/removal checks, and visual confirmation. Parent integration must not run it through Carousel type/tag or claim a free-positioned canvas.

## Entire windshield surface: scope and ownership boundary

The owner asks for the complete windshield drawing surface, including speed, speed-limit signs, warnings and widgets. **B00E is one family of factory widgets, not the entire HUD compositor.** The content-cell findings above must not narrow that objective silently.

The analyzed `HmiMain3D`, `NavNBTEvoController`, `NavigationFully`, `LayerManagerService`, `LayerManagerControl`, Screen, EGL/GLES and OMAP WFD drivers are head-unit artifacts. Captured instances include `pip-layer-car-2026-11-18/router/files/df9caf0fa3dec6b3-LayerManagerService` and `5608ec212adc0714-LayerManagerControl`; output-driver captures include Screen and `libWFDomap5430ES2_0.so`. Their local surfaces, image sizes and layer controls do not establish the windshield receiver's root canvas or ownership.

The saved B006/B00E exchanges terminate at the cluster Ethernet endpoint. They expose structured model/resource services and proven widget visibility, not a parent compositor framebuffer, arbitrary coordinates, z-order, clip rectangles, whole-display resolution, or a complete public layer enumeration. Factory speed/speed-limit and warning graphics remain distinct ownership questions; the door PNG retrieval on B011 travels cluster-to-HU and is not an upload route.

No matching **cluster/HUD receiver binary** is identified among the analyzed artifacts. The existing receiver review specifically distinguishes nonmatching public Bosch firmware examples from the target Supra. This is an evidence limit, not a statement that complete access is impossible. Whole-display work must trace receiver-side ownership and exposed interfaces separately from these bounded widget cell experiments. A larger successful cell image would still not prove access to the main canvas.
