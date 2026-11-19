# Guidance renderer map — 19 November 2026

NavigationFully SHA256 `957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d`. Offline ARM factory and RTTI trace; no vehicle execution.

Factory0x7de844 reads elementtype atrecord+8, subtracts1, and dispatches51table slots at0x7de860. **Seven slots explicitly return null**:19,22,23,24,27,31,45. Therefore there are44accepted typevalues, not51supported renderers. Several share animplementation.

| Type | Renderer class | Constructor |
|---|---|---|
| 1 | CGVTextElement | 0x8167e8 |
| 2 | CGVBoxElement | 0x816fb4 |
| 3 | CGVBitmapElement | 0x816358 |
| 4 | CGVGraphic2DElement | 0x815d18 |
| 5 | CGVStreetInfo | 0x812860 |
| 6 | CGVStreetInfo | 0x812860 |
| 7 | CGVDistanceTo | 0x80dc64 |
| 8 | CGVDistanceTo | 0x80dc64 |
| 9 | CGVDistanceTo | 0x80dc64 |
| 10 | CGVDistanceTo | 0x80dc64 |
| 11 | CGVTimeTo | 0x80d238 |
| 12 | CGVTimeTo | 0x80d238 |
| 13 | CGVTime | 0x80b6e4 |
| 14 | CGVBargraph | 0x80a9b0 |
| 15 | CGVStreetSign | 0x8085a0 |
| 16 | CGVExitSign | 0x807144 |
| 17 | CGVBigSign | 0x804b1c |
| 18 | CGVCompass | 0x809918 |
| 19 | Unsupported/null | — |
| 20 | CGVGuidingSymbol | 0x801834 |
| 21 | CGVIntersectionZoom | 0x7f5ce8 |
| 22 | Unsupported/null | — |
| 23 | Unsupported/null | — |
| 24 | Unsupported/null | — |
| 25 | CGVGuidingBitmap | 0x7e704c |
| 26 | N13NJunctionView22CGVGenericJunctionViewE | 0x7f1848 |
| 27 | Unsupported/null | — |
| 28 | CGVLaneRecommendation | 0x7fac90 |
| 29 | CGVSymbolText | 0x80b07c |
| 30 | CGVRoadDirectionArrow | 0x7ebd60 |
| 31 | Unsupported/null | — |
| 32 | CGVContainer | 0x7ea614 |
| 33 | CGVGraphic3DElement | 0x81536c |
| 34 | CGVBargraphDaimler | 0x8099f8 |
| 35 | CGVRenderContainer | 0x7e9d38 |
| 36 | CGVRenderContainer | 0x7e9d38 |
| 37 | CGVRenderContainer | 0x7e9d38 |
| 38 | CGVRenderContainer | 0x7e9d38 |
| 39 | CGVRenderContainer | 0x7e9d38 |
| 40 | CGVLowGuidingModel | 0x7ecb28 |
| 41 | CGVManeuverHighCCP | 0x7e64a4 |
| 42 | CGVManeuverHighIntersection | 0x7e3324 |
| 43 | CGVCrossingElement | 0x7e3c2c |
| 44 | CGVCCPInfo | 0x7e527c |
| 45 | Unsupported/null | — |
| 46 | CGVManeuverDescription | 0x7e2b98 |
| 47 | CGVManeuverHighLinkList | 0x7e1670 |
| 48 | CGVPlacementContainer | 0x7e80cc |
| 49 | CGVPlacementContainer | 0x7e80cc |
| 50 | CGVLabelContainer | 0x7df7b8 |
| 51 | CGVLaneGuidingModel | 0x7f7948 |

## Pixel-producing candidates and input boundaries

Type3 `CGVBitmapElement`, addresspoint0xa55a38, createSelf0x815e6c, is a genuine bitmap primitive. It copies eight bytes of recordgeometry intoobject+6 (four16-bit coordinates), checks record+0xc sign and context capabilities, constructs graphicalobjects, then passes **record+0x10** to0x886b78 with its context at0x815f94–0x815fa0. Width/height are computed as coordinate differences at0x815fbc/0x815fc4 and stored atgraphicobject+30/+32; localorigin+2c/+2e becomes0. This is not an exposed rawpixelupload: its ID resolution is traced below, while the selected XPD/XRD records remain external inputs.

Type1 `CGVTextElement` has createSelf0x8168dc and updateSelf0x8169f8. Type25 `CGVGuidingBitmap` has createSelf0x7e6970, with explicit `backgroundBitmap`/`arrowBitmap` theme logging. Those distinguish generic stylebitmap from maneuver-derived bitmap inputs; no interchangeableexternalbufferAPI has been established.

Types35–39 `CGVRenderContainer` use createSelf0x7e955c, updateSelf0x7e9894. Native diagnostics name styleRef, childnumElements, per-child boundingbox/type/style, and `renderToBitmap`. UpdateSelf iterates childobjects, invokes their update virtualslot+10, obtains their geometry, and accumulates bounds with16-bit signed coordinate arithmetic. This is the concrete composition path to investigate for PiP pixels. It does not prove destinationwindshieldbinding or an unbounded rootcanvas.

Type42 `CGVManeuverHighIntersection` has createSelf0x7e3644 and updateSelf0x7e35a0. Type48/49 shareplacementconstructor0x7e80cc with explicitmode0/1 respectively. Type50 is aLabelContainer subclass ofRenderContainer. A successfulsessionalone does not choose any ofthese: actualexternal viewStyledefinition must instantiate them.

## Reproduction and remaining data

Private `outputs/canvas-renderer-map-2026-11-19/` contains factorytable, exactpertypebranches, constructordisassemblies, RTTI-derived classnames and methods. `map.py` traverses thetable; its raw vtablecandidate lists can includeadjacentconstructor literals, so thetableabove selects theactualconstructor'sclass (not everycandidate). No receiverpixelclaim comes from RTTI names.

The selectedstyleDBdirectory still must supply concreteelementrecords, styleIDs andXRD resources. Thatfileinput is distinct fromyet-unproven receiverassociation. The bitmap resolver and composition handoff are traced below. External style data remains the precise missing input for selecting a real instantiated style; source-pixel publication and physical receiver binding are separate stages.

## Dynamic image insertion traced further

Generic bitmap binding `0x886b78` stores the requested ID at graphical-object+24 and asks `CGVBitmapManager::getBitmap` (`0x7d8c54`) for a retained image reference. The manager scans 16-byte entries; cache misses with high two ID bits clear schedule styleDB access through `0x894f40`. Nonzero high bits do not trigger that styleDB fallback. Atlas reactivation (`0x7d9350`) obtains an existing atlas subimage; it is not a file upload API.

A separate dynamic path exists. Manager initialization binds a `CGVImageAccess` object at manager+44 (`0x617ae4` → `0x7d644c`). Its constructor `0x89d25c` initializes generated IDs at `0xc0000000`. `CGVImageAccess::addBitmap` (`0x89d514`) increments this counter, saves a 32-byte metadata record, and invokes its callback virtual slot+8 at `0x89d5b8`, supplying the decoded image reference and generated ID. The callback is the bitmap manager's `0x7d80e0`. This explains dynamically populated non-style entries without establishing a public raw-pixel input.

The only direct external callers found for image request `0x89d120` are `0x7e677c` and `0x7e681c`, in type25 `CGVGuidingBitmap`: background and arrow requests use kinds2 and3. Its createSelf `0x7e6970` resolves maneuver data via `0x7de388` → `0x86b894` (variant from `0x7de424`), copies source identity from maneuver-data+94 into element+24, and selects the associated background/arrow themes. The asynchronous `CGVImageAccessJob::process` at `0x89dc2c` obtains an `IImageAccessor` using data-access shared memory and a source handle; its commit `0x89d788` supplies the decoded image to the callback. This is a database-image path. No externally supplied raw-byte field has been proven.

RenderContainer's actual render adapter is `CGVView` virtual slot+18, function `0x61d9d0`, confirmed by RTTI and vtable entry `0xa0e158`. It forwards manager pointer at view+0c, context at view+54, rectangle and primitive vector to `0x611ad8`. That manager operation requires a nonempty primitive vector and calls `0x61167c` to produce a bitmap. The earlier `0x1ed694` in container update releases an old bitmap when bounds change; it must not be mistaken for creation.

These are callable internal pointer-based interfaces, not standalone services. An owned guidance session does not by itself provide a sourceHandle for arbitrary images or grant a renderer-object pointer. No process-memory mutation, code hook, or guessed handle is proposed by this map.

`0x86b894` resolves the current maneuver entry through its array at+19c and returns data via0x5fbc04 only when its capability predicates pass. Source copying0x7e6954 transfers a32-bit value followed by a managed string/reference operation0x4a1b08. The image job resolves the data-access source and obtains an `IImageAccessor` through factory0x89d9a8. Its input contract is therefore source identity plus image/theme data, not an arbitrary byte vector. The two direct request sites use background/arrow kinds2/3; no third direct caller was found in the captured executable. Indirect callers are not excluded.


## Output capability map: local pixels versus physical display

The primitive type numbers above are **not** the following displayable output types. The two enumerations belong to different factories.

Displayable factory `0x88249c` accepts output types 0, 1 and 3; type 2 returns null. Constructor `0x881d48` allocates the corresponding backing object. Geometry is narrowed to signed 16-bit coordinates. That representation does not establish a supported maximum allocation or windshield size.

| Output type | Exact implementation | What is established | What is not established |
| --- | --- | --- | --- |
| 0: window | `0x8813e0` → `0x8831a4` → `0x882e94` | Owned KD/EGL window; requested width/height; `WindowCaption` defaults to `MapGV`; separate `ScreenNumber` option | LayerManager admission, physical display selection, or windshield ownership. Caption 1056 is not hardcoded here. |
| 1: bitmap | `0x88125c`, bitmap output `0x88d7a0` | Owned offscreen EGL surface; `GVBitmap_%d` shared-memory output; actual readback and optional `NBT_RLE32`/`NBT_RLE16` compression | Raw-pixel input API, complete selected view definition, or a receiver job binding this output to the windshield |
| 3: command buffer | `0x8811e4` → `0x880dec` | Owned command-output object; separate publication path | A raster framebuffer or interchangeable type-1 pixel receiver |

Type 1 publication is concrete: `0x881f5c` calls `0x88d634`, which reads graphics pixels via `0x8606f4`, sizes shared memory with `0x88cf88`, and writes bytes via `0x88d184`. Descriptor `0x8a12b8` uses width×4 stride for format 0, or 64-bit-aligned 16-bit-pixel stride for format 1; stride is stored as a 16-bit value. These are implementation constraints, not safe size limits. Type 0 does not publish through this Data path.

The 24-byte native metadata record contains supplied **user ID**, shared-memory name, maneuver ID, guidance type, byte count and sequence. It is not an allocated displayable-session identifier followed by view IDs. Producer `0x88b79c` queues the property; observer `0x1f4aa8` forwards the nonempty record vector to the provider. Data event `0x80000004` is independently verified by the controller accessor and serializer.

Controller displayable registration `0x311488` requests Data updates. Proxy `0xc27428` registers `0x80000004` using `CHBRegisterProxyBase::setRegistryNotification` and the upcoming method-4 request sequence. Captured framework implementation `0xb1010` sends generic request type **0x105**, with that update ID and registry ID. The same sequence is then used for DNAVI method 4. This is a framework registration, not an invented DNAVI method 5 or a global Data subscription. It provides an evidence-backed way to observe an owned producer independently of factory user ID `0x258`.

Destructor `0x8815d0` detaches the graphics surface, destroys its EGL surface, and releases owned window/bitmap/command objects. DNAVI displayable unregister method 6 (guidance unregister is method 7) and framework listener removal must still complete; object destruction alone is not proof of remote image disappearance.

## Cross-check against B00E and the full windshield

The latest [content-binding results](CANVAS-BINDING-LIVE-2026-11-19.md) supersede the earlier untested content-cell candidate. Both Carousel content words and both tested Entertainment cells accepted/restored their models and resources, but **no custom ruler was visible**. The corresponding station text disappeared, proving the intended field was targeted without proving image decoding or rendering. A no-bitmap, all-absent-reference Carousel reproduced the empty rounded frame. That frame is a factory widget decoration, not our pixels.

NavigationFully's `CGVGuidingBitmap` is a different mechanism from HmiMain3D's B00E bitmap-resource producer. It requests maneuver/database images using source identity, theme and background/arrow kind, then allocates internal IDs beginning at `0xc0000000`. B00E uploads and resource IDs have no demonstrated link to this manager. The new trace therefore does **not** explain the failed B00E receiver binding, authorize moving an ID between services, or justify another size ladder. SetContent variant 4 is also not an image upload: its traced payload is three words, with the first stored in a list keyed by the third; the second is ignored in the examined handler.

The whole-HUD Height corner outline is separate from the radio frame. The saved E0/01 observer recorded two CA6 adjustment messages, mapping to UI height −1→0, not pixel buffers or the separately traced setMode call. Neither outline exposes its interior as an arbitrary canvas. Speed, speed-limit and warning graphics remain part of the physical receiver/compositor investigation; no full-screen dimensions, free-positioning API, clipping contract or z-order ownership follows from the local guidance renderer map.

Actual ECU60 inventory is now captured in [receiver identity results](RECEIVER-IDENTITY-RESULT-2026-11-19.md). Missing identity is no longer a reason for another trip. Matching target receiver code and the link between its compositor and the HU producer remain separate evidence requirements; nonmatching BO03 firmware addresses cannot fill them.

## Exact remaining inputs and proposed test order

1. **Decode the selected external style data before another drawing attempt.** Preserve the coherent `/opt/nav/eceusa/bin/gvStyleDB_ID5_NBTEvo_BMW_USA_1025` directory/index, `style_config`, and selected `nav_styles.ini`. Resolve category 4/variant 0 to its XAR and the exact `guiding.*.viewStyle<ID>` definitions, linked XRD assets, geometry and actual element types. The decoder is prepared; constructed fixtures establish parser behavior, not a usable installed style.
2. **Prove owned source pixels first.** Using a supported definition and validated broker route, create an owned type-1 output with the framework Data registration described above. Observe matching user ID, byte count and advancing sequence; read and decode only its named shared memory. This is an HU producer test, not a windshield test. A distinctive cross/IU fixture is meaningful only after an actual supported custom-content input is established; do not substitute guessed source handles.
3. **Prove the consumer/job binding before requesting visible space.** Resolve the actual receiver association, required output type, style and lifecycle. A type-0 window or type-3 command stream is not interchangeable with the proven type-1 byte output. Keep caption, user ID, allocated session, registry sequence and physical destination distinct.
4. **Only then perform one bounded larger-display test.** Verify known V1 cleanup, owned-resource admission, marker identity, measured geometry and complete removal; restore V1 afterward. Do not rerun the failed B00E field substitutions at larger sizes or reuse factory ownership merely because registration was acknowledged.

This order separates a bad source image, missing source rendering, missing transport subscription, and missing physical destination binding. It does not claim the final larger-display test is ready today. All work in this map is offline; installed V1 and its startup remain unchanged.
