# Native map-window bounds: input, clamp and destination

20 November, offline. This is an actual rectangle-control chain in captured vehicle binaries, not a claim that the windshield root canvas is unlocked. No V1 or vehicle changes.

## Controller input and dimensions

In NavNBTEvoController (SHA256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`), `requestSetVisibleViewPort` constructs an x/y/width/height rectangle, calls `0x754420` at `0x7622f0`, then copies the result into owner+0x15c at `0x762348..350`. The clamp caps width and height against owner+0x174/+0x178; it does not change the origin.

Initial dimensions are populated at `0x766f4c..0x766fa0` through `getPhysicalScreenSize` (`0x7546f0`) using owner+0x1c. Its explicit native branches are:

| Selector | Native label | Dimensions selected from coding |
| --- | --- | --- |
| 1 | MAIN | 800x480, 1280x480, or 1440x540 |
| 2 | ASSIST | 480x480 or 540x540 |
| Other | RSE | 800x480 or 1280x720 |
| Missing coding | Fallback | 1440x540 |

These are producer screen categories, not a measurement of this Supra's windshield. There is no explicitly named HUD branch in this function. Do not equate MAIN with the main windshield canvas merely because both use the word main.

`setVisibleViewPort` at `0x757fa0` passes the stored rectangle to helper `0x7463d4`, queues work through `0x7445e0`/`0x74612c`, and reaches `0x320950`. That function logs `SetWindowPositionAndSize`, forwarding all four coordinates and three animation floats to `0xc24540`. The generated proxy names **DNAVIMapCanvas** and uses method **0x24**. This is not B006's road-list model.

## Captured provider and local window

The matching service implementation is in **NavigationBasic**, SHA256 `d03464928749857ceab8daec20db422cf81d47f722ae4bb9d9c54a03057c1206`. NavigationFully's previously traced guidance displayable is a different path.

Basic dispatch `0x87e8e8` reaches request dispatch `0x87d4e8`; table `0x87d528[0x24]` selects `0x87e234`. The server virtual call reaches `0x87ab70`, then owned session implementation `0x747a1c`. This allocates `CCmdSetWindowPositionAndSize` through `0xa12414`. Command execution `0xa12368` resolves its map view and calls `0xa2ab90`.

The view's window is changed through `0xdbb224`: width/height at window+0x18/+0x1c, origin at +0x20/+0x24 and dirty flag at +0x38. RTTI identifies `NGraphicsSystem::CWindow`. The view then updates camera settings through `0xa2a988`. This establishes a local map-window geometry control. It does not establish a receiver-owned windshield clipping rectangle or a B009 HUD0 binding.

## Actual ARM execution

Two offline verifiers execute the captured instructions under hash checks:

```sh
python tools/verify_mapcanvas_bounds.py /absolute/private/NavNBTEvoController
python tools/verify_mapcanvas_window_rect.py /absolute/private/NavigationBasic
```

Use the existing analysis environment with Unicorn and pyelftools. No software installation or vehicle connection is needed.

- Controller clamp: five cases cover unchanged dimensions, both dimensions oversized, dimensions inside the limit, width-only oversize and height-only oversize. Origin and adjacent guards remain intact. Only the known logging call is intercepted; any other external instruction fails the check.
- Basic window setter: three cases cover translated/non-square geometry, unchanged geometry and an already-dirty window. The entire guarded object matches the expected four fields and dirty flag; zero external calls are intercepted. These are synthetic inputs to actual instructions, not an emulated vehicle or receiver.

## Consequence for the next batch

Keep this API out of the live batch until its window/output binding is connected to the desired windshield destination and an owned-session restoration contract exists. Increasing these source dimensions alone cannot be presented as increasing the windshield bounds. The optional narrow-tail test remains available under [the next-batch plan](HUD-NEXT-CANVAS-BATCH.md); this trace does not replace it with an unproved factory-window mutation.
