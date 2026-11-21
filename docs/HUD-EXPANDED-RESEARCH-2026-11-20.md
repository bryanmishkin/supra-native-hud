# Expanded offline research and next-trip preparation — 20 November 2026

The next-trip batch has three prepared cases: dim RGB, grid/circles, and a newly added conditional five-row/thirteen-column measurement pattern. The first two test activation and bitmap rendering of the separate408×132 TestBmp surface; the third measures its visible extent using exact factory reference marks. This is not arbitrary uploaded-image access. Installed008 behavior remains to be measured; the executable research uses hash-pinned004 firmware. No vehicle contact, V1 installation change or startup change occurred in this work.

Use [the next-trip card](HUD-NEXT-TRIP-CARD-2026-11-20.md) and [exact execution/cleanup procedure](HUD-DIAGNOSTIC-SURFACE-TEST-2026-11-20.md). Do not run the third case if the first two show only the familiar strip. Do not add random patterns simply to increase test count. Previous destination-picture, narrow-tail and frequency tests remain closed.

## Actual packaged image access

Native package parsing at0x313078, string-table loading at0x313340 and typed-tree construction at0x31341c establish the asset format. The bitmap tree is descriptor index3/type7: table0x2a6b0, payload base0x3014c,1057 entries. Each entry carries a string key, two child offsets and a payload offset. Names come from the string table at0x220; payload headers must repeat the same name key. This avoids equating unrelated scene ordinals with bitmap ordinals.

`extract_hud_test_assets.py` reconstructs these exact tree links in synthetic memory, then runs native0x31394c and its real string comparison to the successful selection branch at0x313a28. All26 TestBmp names select the exact corresponding package record without hooks. Python zlib extraction then yields408×132 RGBA images. The package, executable and each pixel buffer are hashed. Native stream I/O, GPU construction and physical rendering are not emulated. Proprietary extracted references stay in the private archive, not Git.

Selector0x5c contains the border, grid and three circles. Selector0x5d contains five marker rows across thirteen columns with a center cross, providing useful outer-edge observations after successful tall rendering. Selector0x5f is another grid and0x5e is dense noise; neither is added to the live batch because it does not answer a sufficiently distinct question. The exact private references accompany the batch.

The existing named-asset provider trace connects TestBmp to DefaultAssetProvider, cached-name lookup and registered package search. The externally uploaded RIC numeric resource cache is separate. Successful insertion, decoding and synthetic brush replacement do not provide an external binding instruction for this scene node.

## Separate built-in HUD picture command

`imgviewHUD` at0x154aa6 delegates name lookup to0x155ed0. Native execution tests all45 table names with bare, Unix-prefixed and Windows-prefixed names, plus seven negative inputs:142 cases pass. The lookup removes path prefixes and searches a fixed table. A path-like argument is not filesystem image loading.

Forty-three built-ins are1280×480; the two HUD records are480×240 (`480x240_TestHUD_red` and `480x240_TestHUD_text`). The command selects the local HUD display driver `imx6_rgb_ipu2`. This is a separate local display route, not proof that uploaded RIC images can enter it.

A debug parser at0x153a24 recognizes FE60 enable/disable and FE61 command payloads. The higher dispatcher at0x13dcf2 in the captured mode1 state filters a different FE80..FE81 range before this parser. Consequently a string found in firmware is not sufficient evidence of an externally reachable command. No live debug-tunnel, session-change, unlocking or guessed-command test is admitted; command lifetime and cleanup are also unproved.

## Remaining uploaded-image consumers

Direct calls to uploaded-cache getter0x2b21fe occur in KIListCarousel3D, KIList2D, KIListHud2D and KITable2DBase. The HUD list path at0x246672 reads bound Rectangle dimensions, looks up the numeric resource and forwards its dimensions/data to0x25740c. The table path similarly reads a Rectangle at0x24fe36, looks up the cache at0x24fe6c and forwards data at0x24ff36. Incoming bitmap size does not replace the target Rectangle.

`verify_hud_list_image_gates.py` executes the actual column-selection branch at0x2b059e for all five columns:0/4 select bitmap copying,1/2/3 select text copying. It also checks the six image rectangles in the hash-pinned HUD scene. Both list and table contain three28×28 icon nodes at(158,35),(158,67),(158,101). These are separated icons spanning94 vertical units, not a contiguous408×132 image surface. Parent visibility and runtime layout are not proven by these serialized dimensions. No repeated menu-image test is added from this finding.

## Coverage and next evidence

| Area | Evidence obtained | Consequence for next trip |
|---|---|---|
| External TestBmp activation | Native auxiliary registration, parser, dispatch, record copy, state gate, start/stop completion | RGB and grid cases prepared; identity and stop preflight required |
| TestBmp physical extent | Two408×132 serialized nodes; actual assets now extracted and name-verified | Measurement case added after taller activation; physical extent remains unmeasured |
| Uploaded image bytes | Native cache insertion/read, RLE decode, guard checks and geometry fit already pass | Marker ready offline; no external TestBmp binding found |
| Asset provider/package access | Cached lookup/removal, concrete provider, package tree and actual names traced | Factory asset route established; numeric upload cache remains distinct |
| Built-in480×240 pictures | All45 names and basename behavior executed; local HUD driver identified | No external command/cleanup contract; no live tunnel probe |
| List/table image paths | Actual cache consumers, column branch and six28×28 targets checked | No full-surface test justified; previous text-column substitutions not repeated |
| PiP sink selection | Native destination metadata, policy and visibility gates traced in prior evidence | Existing cluster-only outcome does not justify another identical PiP trial |
| Resolution/height controls | Receiver ignores resolution arguments on traced Ethernet path; height is scalar adjustment | No resize or Hz repeat |
| Retained Ethernet captures | Application routes and service advertisements reviewed; UDP audit found no new receiver image stream | No fabricated protocol or service IDs |
| Installed receiver differences | Installed008 identity pinned; research004 is older | A102 compatibility is an explicit live hypothesis; no firmware addresses patched |

The local-data PiP writer/external activation connection and arbitrary uploaded-image binding to TestBmp remain unresolved. This report does not claim every conceivable research path is exhausted. It records the concrete inspected areas and prevents dead ends from becoming another car test. Further conclusions require new causal evidence, especially installed-receiver behavior from the prepared batch; no need to repeat the completed strip tests.

## Validation and preservation

Eight native A102 cases pass including the new selector0x5d, negative state/length/subfunction paths and stop. Eleven host runner tests pass, including all three cases with successful completion and lost start acknowledgement followed by cleanup. All256 renderer selectors and enable2 withdrawal were already checked. New native checks add142 name-lookup cases,26 package-name matches and five column branches, plus six serialized rectangles. Reports explicitly distinguish native execution, synthetic state, Python extraction and unexecuted physical rendering.

V1 source/runtime installation is not modified by these changes. Its last recorded runtime state is intentionally paused at the owner's request, not restored. Before and after the next admitted car batch, compare all15 installed files as required by the existing procedure.
