# Next session: locate usable V2 drawing areas

**No Hz tests. V1 stays installed unchanged.** The purpose is to fill the [whole HUD capability map](HUD-CAPABILITY-MAP.md): actual image placement, usable extent, scaling/clipping, display destination and cleanup. Main HUD ownership remains a separate target; a widget result must not be called fullscreen access.

## Offline package now available

- Corrected Carousel runner replaces one content reference, not the separate icon. Both content fields have a factory bitmap-producing path.
- Entertainment codec replays 180 actual factory models exactly. The same bounded runner supports model0x66/type0x16 with an explicit table row/content column.
- 36,64,96,128 square cross and IU fixtures for both models. Thirty seconds per visible case, counted after acknowledged posting. Independent cases do not stop merely because another layout is blank; uncertain cleanup always stops further drawing.
- Original snapshot, exact candidate bytes, upload/presence replies, focus, commits, restoration, disposal and final absence are retained.
- Fixture snapshots are historical offline inputs. They never satisfy next-session admission.

## One session, priority order

1. Verify installed V1 baseline/runtime and collect existing startup/fault evidence before resets. Record the main interface/provider/advertised-model inventory from this same boot; compare against saved data rather than redownloading unchanged binaries.
2. Start a bounded passive recorder before owner actions. Capture the full source Carousel using MODE, then the station-list Entertainment model. Save successful focus/commit and idle withdrawal for each. Read and validate both exact bodies immediately. Do not treat only a source menu as coverage of both layouts.
3. Pause V1 cleanly. Verify factory overlays closed, idle focus committed, snapshots from this boot, bitmap pool available, and known recovery. No changes to startup, enabled tokens or installed workers.
4. **Binding block:** Carousel selected content field1 then field2; Entertainment content column1 then column2 at an explicitly identified visible table row. Use distinct36×36 cross and IU images to distinguish rendered pixels from a factory frame. Preserve all other model content/state. A historical row0 fixture does not prove row0 is currently visible; first correlate the exact factory table with the displayed labels. Blank output on an unlocated row is inconclusive.
5. **Area block:** For each working placement, try64,96,128 with a complete border/cross. If128clips after64works,96bounds the transition. Do not repeat a failed binding at larger sizes. Record natural scaling versus fixed physical extent, aspect ratio, missing border edges, widget bounds and location relative to speed/limit. Use the same fixed camera view where practical; photographs measure apparent proportions, not native HUD resolution.
6. Confirm the IU at the largest unclipped size. Record windshield and cluster separately, colors and whether the factory icon/text remains. Do not infer transparency from opaque black backgrounds; alpha behavior is unverified and not part of this opaque-image package.
7. Withdraw focus, restore each exact current factory model, then remove only the tracked bitmap and check absence. Once all tests finish, restart normally, verify unchanged V1 files/configuration and advancing RPM/heartbeat, and confirm V1 visible before unplugging.

Start with binding and the first working area's size ladder. Extra size cases are conditional, not mandatory repetitions. Budget depends on observed results; do not spend the session on throughput or unrelated radio/navigation endurance campaigns.

## Main windshield surface: data question, not another blank-image attempt

The source/entertainment cases above map two receiver-rendered widget placements. They do not address arbitrary x/y, root resolution or z-order. During the same session, retain all services and provider metadata in the existing passive recordings, plus complete existing startup configuration replies. Main HUD controls traced offline include ControlHUD2, StatusHUD2 and ControlHUD2KOMBI registration values410/411/415. These values are **not authorization to send guessed requests** and their current network route is not verified.

Before any main-surface drawing test, identify the receiving implementation/API, accepted image or primitive format, dimensions/placement contract and reversible removal. No root-canvas sender exists in this kit. The main surface, speed/limit, warning and alignment regions remain explicitly unresolved in the capability map; do not declare the whole investigation complete after a content-cell success. Existing height/door/voice/phone recordings must be analyzed before requesting repeats.

## Commands

Offline generation, from repository root:

```sh
python3 tools/prepare_canvas_binding_tests.py \
  --snapshot /absolute/path/current-or-historical-carousel-model.bin \
  --entertainment-snapshot /absolute/path/entertainment-model.bin \
  --output /absolute/path/new-offline-kit
```

Live invocation only after current admission and verified local forwarding:

```sh
python3 tools/b00e_bitmap_trial.py --execute --port "$VERIFIED_LOCAL_PORT" \
  --admission "$CURRENT_ADMISSION" --bitmap-bgra "$MARKER_BGRA" \
  --size 36 --content-field 1 --output "$NEW_CASE"
# Entertainment: use that model's admission and --row R --column C instead.
```

Admission uses `restore_model_body_hex` (legacy `restore_carousel_body_hex` remains accepted), the exact recognized B00E configuration and the existing current-session assertions. A snapshot must contain no tracked test RID in any original resource reference. Entertainment rows are transmitted-array indices, not guessed selected station numbers. Columns start at1 for content; column0 is the separate icon and rejected.
