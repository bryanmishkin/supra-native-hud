# Viewport boundary consumers: verified exclusions and remaining target

20 November 2026. Offline only; V1 installation and application code unchanged. This supersedes the suggestion to use right alignment as the next larger-canvas test. The owner requires a changed usable drawing extent, not another arrangement inside the existing road-list area. No Hz tests.

## Newly traced consumer, not a guessed dimension

Captured HmiMain3D SHA-256: `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`.

`CPxyKombiInterface::CKombiExternalDisplay` is not established as an external image surface. Its three scalar fields must not be interpreted as a width/height pair because two have a 4095 wire bound.

| Field | Getter | Actual traced consumer | Conclusion |
| --- | --- | --- | --- |
| `+0x78` u16 | `0x2305ef0` | No direct BL caller found in this binary's ARM `.text` scan | Unknown; indirect consumers remain possible |
| `+0x7a` u16 | `0x2305eb4` | `0xfea520`, in the `CDevCarOnBoardComputer` implementation; valid values <=4000; 4093 clears a validity flag; stores into an on-board-computer data record | No width/viewport setter demonstrated; precise data label remains unresolved |
| `+0x7c` u16 | `0x2305e78` | `CDevCarTemperature` callback `0xf35608` stores values <=416; formatter `0xf357d4` converts them to temperature strings | Temperature, not canvas height |
| `+0x80` enum | `0x2305e3c` | Same temperature callback accepts enum 0/1 | Not a demonstrated display-destination selector |

The proxy vtable is `0x39c3348`; GOT relocation `0x39ea7f4` identifies its constructor reference. Constructor code places this child at parent `+0x101c`. Both consumers retrieve exactly that child. The temperature caller is `0xf35630`; the on-board-computer caller is `0xfea5d0`. This establishes the field-to-consumer chain rather than associating adjacent strings with unrelated functions.

The temperature formatter uses `(raw-80)/2` with truncation toward zero and a decimal argument `(raw & 1)*5`; raw79 has a separate `-0.5` literal. This is not pixel geometry. `verify_external_display_semantics.py` executes the three native getter tails and eight arithmetic cases with no intercepted calls, and checks the special literal. It deliberately does not claim to execute the validity guard, string library, entire consumer or receiver.

## Resolution notification is not a rectangle

`CPxyNavigation::CNav_KombiResolutionChange` vtable `0x39c9750` resolves through GOT `0x39ea7cc`. Construction installs the child at parent `+0x84ac`; registration `0x23890e4..0x23890f4` assigns identifier `0x0cff`.

Dispatcher `0x2357a48` reads one byte bounded 0..1 and passes that byte to callbacks at child `+0x8c`. No coordinates or dimensions are read in this dispatcher. A downstream callback could select a predefined layout; this trace does **not** prove that no such callback exists. It does rule out treating this payload itself as arbitrary width/height or sending invented dimensions to it. Direct parent-offset scans found proxy lifecycle/registration uses, not a resolved graphics consumer.

## Which boundary is actually still missing?

| Domain | What is known | What it does not establish |
| --- | --- | --- |
| V1 bitmap | Advertised maximum 150x36 per resource | Outer road-list viewport dimensions |
| Road-list entries | Separate entries put both images in windshield; second is partially visible | Editable clipping rectangle or full HUD canvas |
| Road-list alignment | Producer names values Left/Right | Enlargement |
| PiP resource | Advertised maximum 320x320 | Windshield destination or viewport |
| Native PiP output | Custom pixels visible in cluster, selection1 with 460x237 tuple | HUD selection0 or forwarding of those pixels |
| HUD height outline | Factory corner/frame graphics are visible | A client-uploadable image target |
| ExternalDisplay scalars | Temperature and on-board-computer consumers above | Root graphics bounds |

The receiver-side road-list layout/clip implementation has not been located in the captured head-unit executables. These are producer binaries, not the matching cluster receiver rasterizer. Photo clipping alone does not distinguish software cropping from the HUD optical viewing region. No exact native HUD rectangle can be inferred from camera pixels.

## Next test must change extent, not placement

Do not call the existing `right_boundary_ruler` kit the next larger-display test. Keep it as a historical, unexecuted alignment experiment only. Do not request another car session for it under the larger-canvas goal.

A qualifying candidate must identify either (a) a traced control of the receiver's width/height/clip, or (b) a separate image surface with a supported windshield attachment. Its static test image must include distinguishable content outside the V1 footprint, with the original footprint retained as a reference. Source dimensions alone are insufficient: no enlargement is accepted until those outside markers are visibly displayed. Preserve V1, use owned resources, journal actual receiver selection, and retain proven withdrawal/removal before enabling a live candidate.

No qualifying live candidate is enabled by this revision. In particular, it does not send oversized road bitmaps, change undocumented vehicle settings, force a false destination completion, or turn arbitrary scalar fields into coordinates. The requested larger-canvas test remains unfinished; this document must not be presented as a completed fix.

## Reproduce offline

```
python tools/verify_external_display_semantics.py /private/HmiMain3D
```

Requires the existing Unicorn/pyelftools analysis environment. The verifier rejects any other binary hash. Private disassembly, pointer/caller scans and output live in `outputs/hud-boundary-consumers-2026-11-20/` in the workspace and its Drive archive; no captured firmware is embedded in Git.
