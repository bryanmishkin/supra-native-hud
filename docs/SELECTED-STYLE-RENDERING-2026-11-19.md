# Actual selected guidance rendering definitions

Offline analysis of the selected 19 November capture. No vehicle connection or V1 change. `catalog_guidance_styles.py` decodes 210 named view definitions from the captured headers and XPDs, retains raw words, follows style properties and resolves direct bitmap ImageProperty references. Input bytes must match the capture manifest. `verify_captured_style_catalog.py` executes NavigationFully's actual ARM XPD lookup at 0x6366d0 on these captured files: **all 210 offsets match, with no intercepted callbacks**. This validates selection, not a simulated physical HUD.

## Concrete geometry and renderer selection

| Definition | Header coordinate pairs | Actual elements | Meaning for testing |
| --- | --- | --- | --- |
| HUD PiP junction 8301 | (0,0)–(800,480) | Type26 GenericJunctionView, (0,12)–(277,172), style8301 | 277×160 junction element; not an 800×480 uploaded bitmap |
| HUD PiP high-guiding 8402 | (0,0)–(800,480) | Type21 IntersectionZoom, (0,1)–(277,161), style8402; Type20 GuidingSymbol, (25,86)–(92,146), style8403 | Maneuver-driven intersection plus a separate symbol layer |
| RIC dynamic 9403 | (0,0)–(320,320) | Types41,44,6,5,8,7 | Navigation model/text/distance composition, not a blank 320×320 raster |
| RIC static 9404 | (0,0)–(320,320) | Types40,43,46,51,44,6,8,7 | Another structured navigation model composition |
| L7 HUD RGB high-guiding 7402 | (0,0)–(408,116) | Box, intersection, bargraph, distance, lane and street elements | Definition present; selection on this physical receiver remains separate |
| L7 HUD FPK high-guiding 11402 | (0,0)–(408,116) | Similar primitives, with renderContainer11302 | Container expands into street-info content, not arbitrary pixel input |

Pairs are decoded signed 16-bit coordinates; element geometry layout agrees with captured native createSelf memcpy and endpoint arithmetic. Header dimensions describe stored definitions. They are **not** a physical allocation, scaling guarantee, maximum canvas, or permission to cover speed/warnings.

## Followed resource references

- 8301 resolves `guiding.styleRef8301.junctionView`.
- 8402 resolves `guiding.styleRef8402.izStyle` and associated route-line/destination-flag settings.
- 8403 resolves its own guiding-symbol table. This is separate from intersection image pixels.
- Container7301 resolves `renderContainer` to junction renderer26 plus street-info renderer6. Container11301 contains junction renderer26/style7301. Container11302 contains street-info renderer6/style11193. These are composition instructions, not an external image pointer.
- Direct type3 bitmap elements are present in the inspected CID views402/412. Their IDs320600/320602 resolve in ImageProperty to540×485 and480×431 respectively. HUD PiP views8301/8402 contain no direct type3 element. CID asset existence does not route it to the windshield.
- ImageProperty has attributes; the selected directory's XAR entries are XPD, not captured XRD pixel payloads. Do not treat an attribute record as image bytes.

## Native input dependency

Type26 createSelf at0x7f16a8 first resolves maneuver context via0x7de388, loads its style, and asks0x86b8f4/0x7df654 for maneuver data. At0x7f1798 a null result goes to0x7f17ec, calling context-update handling0x7de340 instead of the rendering path0x7f0fc8. A valid style alone therefore does not imply an available junction image.

Type21 createSelf at0x7f57b4 loads styleRef through0x7f193c (accessor virtual slot0x58), copies the actual element rectangle, checks style validity and resolves maneuver/variant data. Its style is not an external raw-byte input. The separate dynamic bitmap manager path already traced in GUIDANCE-RENDERER-MAP.md remains a data-access image request, not a demonstrated upload API.

These facts explain why a registered producer or an800×480 declaration alone is insufficient. They do **not** retrospectively prove the exact cause of the earlier arrow-only test, which used a different partially established binding.

## Evidence-driven next implementation

The owned producer test must record registration result, exact selected definition, matching owned Data userId/sequence, actual nonempty pixel bytes and removal completion independently. Style8301/8402 with a dummy maneuver cannot be presumed to supply a marker. Resolve a supported content input or owned renderable definition before asking for a windshield marker trial. Keep output type1 bitmap publication distinct from type3 command output, and from renderer type3 bitmap primitives.

No new car session is requested by this analysis. The owned service bootstrap, usable custom-content input, receiver binding and asynchronous removal still require work. The larger-display marker is not yet executable. No Hz tests or V1 modifications are part of this work.
