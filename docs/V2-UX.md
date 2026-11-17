# V2 UX development

Branch: `v2-ux`, based on `v1.0.0-gold-master`. The installed V1 Gold Master remains the reference baseline. V2 is an offline candidate, not installed or accepted on the car.

## Design direction

The owner supplied [this reference](design/v2-reference.png): a curved segmented cyan-to-orange/red tachometer, five centered shift lights, white RPM and signed PSI values, subtle labels and a divider. The first implementation keeps the proven **150 × 36** canvas, shared-session protocol, and V1 factory-priority contract.

![Exact V2 renderer previews](design/v2-150x36-preview.png)

These are actual C++ pixel outputs enlarged with nearest-neighbor scaling, not a photograph or projected-HUD proof. The reference has much more resolution and a taller aspect ratio; its glow, typography and proportions cannot be reproduced literally in the current canvas. The refined candidate removes stepped italic RPM glyphs and the small RPM label to restore V1-sized digits. Rounded seven-segment strokes and arc/shift-light edges use 4-by-4 coverage sampling into the same opaque native pixels; this adds edge shades, not display resolution. The candidate uses a shallow arc, 20-pixel-high upright RPM digits, a smaller PSI readout, and five steady shift lights. Inactive arc segments remain dim; the lit amount follows RPM.

The cyan/orange/red palette is canonical BGRA. The existing measured red/blue boundary correction still applies in the transport. V2's cyan projection and tiny labels must be judged on the actual windshield; offline appearance does not prove readability.

## What is implemented

- `tachBitmapV2(Frame)` in `src/tach_bitmap.cpp`, leaving classic/sport output unchanged.
- Bounded 150 × 36 opaque pixel output; no geometry, session or resource-ID changes.
- Comma-grouped RPM, central shift cues and signed one-decimal PSI display.
- Unavailable/non-finite/out-of-range boost renders `--.-`, not zero or invented telemetry.
- Demo-only `v2` selection with optional explicitly synthetic PSI.
- Reproducible preview generator and native renderer checks.

The persistent worker **still calls `tachBitmapSport`**. This branch does not silently change the installed/default runtime to V2. The C++ `Frame` already supports boost visibility/value, but the live worker currently reads RPM only. A displayed simulated PSI value is not evidence of a live boost source.

## Reproduce offline

From the repository root, with a C++ compiler and Python/Pillow:

```sh
mkdir -p build
c++ -std=c++98 -Wall -Wextra -Werror -Isrc \
  src/hud_core.cpp src/tach_bitmap.cpp tools/tach_bitmap_demo.cpp \
  -o build/tach-bitmap-demo

# Unknown boost: dashes.
build/tach-bitmap-demo 4250 build/v2-rpm.bgra v2

# Synthetic display value only; does not read or command a vehicle.
build/tach-bitmap-demo 4250 build/v2-simulated-boost.bgra v2 12.4
python3 tools/render_v2_preview.py build/tach-bitmap-demo build/v2-preview.png
```

The demo's accepted PSI range (-30 to +60) is a formatting bound, not a vehicle operating limit. Existing 7000 RPM scale and 6500 shift cue remain display settings, not newly validated engine limits.

## Development order

1. **Current space:** refine readability, visual balance, arc shape and color progression offline. Review native-size/enlarged previews before a parked comparison. Preserve the V1 output and Gold Master tag.
2. **Live integration:** add explicit renderer selection, build/audit the QNX candidate and validate bounded draw/cleanup before considering a persistent change. Keep the proven double-buffer update and pre-send factory handoff. No full-graph rebuild per frame.
3. **Boost:** identify and verify a fresh pressure source and units/reference. The core can calculate gauge PSI from paired manifold/ambient kPa, but the worker has no such acquisition path yet. Do not label absolute pressure as boost or restamp stale data. Test missing/stale-source behavior and maintain RPM timing. Until then use dashes for actual operation.
4. **Larger space:** first review the existing captured geometry/model evidence and receiver limits offline. Define one explicit bounded geometry candidate, exact image binding, absence/cleanup checks and rollback. A larger bitmap upload alone does not prove a larger visible surface or windshield-only routing. Validate dimensions, clipping, both displays and factory handoff separately from telemetry changes.

Do not request another broad discovery trip merely to redraw pixels. A future car session should have exact candidates, expected visual differences and removal checks prepared ahead of time. The existing canvas is the first deliverable; expansion is not presumed successful.

## Initial verification

- Native bitmap tests pass under address/undefined-behavior sanitizers, including hidden/invalid clearing, opaque geometry, missing/invalid boost and isolation of boost changes to the right readout.
- Twelve classic/sport outputs at 650/4250/5500/6200/6500/7700 RPM match the Gold Master byte-for-byte.
- Five preview frames pass the corrected RLE32 encode/decode round-trip.
- Invalid demo RPM/PSI and PSI supplied to a non-V2 style are rejected.
- All 244 Python regression tests pass in the prepared environment with `pyelftools`.
- No QNX target execution, vehicle display test, boost acquisition or larger-surface proof is claimed by this change.
