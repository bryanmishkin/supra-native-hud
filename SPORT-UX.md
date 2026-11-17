> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

Live update: the initial colored frames projected blue shift lights. A red/blue channel swap at the display boundary corrected them: Bryan confirmed one orange at 5500, three orange/one red at 6200 and five red at 6500. Select `--swap-red-blue` for this Supra road-icon path, including live frames; canonical renderer previews remain BGRA and the RLE algorithm is unchanged. See SPORT-LIVE-RESULT.md for complete live evidence and limitations.

# Sport HUD layout — 16 November 2026

Implemented an optional S2000-inspired sport layout in the native C++98 renderer: rising 24-segment sweep, 20-pixel-tall RPM digits (previously 10), and five enlarged progressive orange/red shift lights. All drawing remains inside the measured 150×36 bitmap. No flashing animation. Classic layout remains the default comparison.

The recovered mockup brief requests an upper RPM sweep, shift cues and retained factory speed. The original mockup image was unavailable in retrieved context; this implementation follows that brief rather than claiming exact image matching. Removing the factory circle does not establish a larger bitmap or independent surface. Additional space below our bitmap remains unproven.

## Use and next parked comparison

`tach-bitmap-demo RPM OUTPUT.bgra sport` generates the exact new pixels. Existing calls without a style preserve the classic output. The live trial accepts `--renderer-style sport`; combine with the already verified `--graph-variant empty-direction-zero --double-buffer` and the existing explicit stopped-guidance and connection arguments. No deployment or vehicle contact was performed for this change.

Compare the new layout at idle for 30 seconds: readability, projected orange/red fidelity, no symbol, no flashing. Check removal from both displays, then factory navigation and radio. Synthetic 5500/6200/6500 frames can validate color progression without revving the engine. The demonstration scale remains 7000 and shift cue 6500; these are illustrative, not validated vehicle limits.

## Validation

Native renderer assertions cover geometry, alpha, orange/red channel order, shift lights and hidden-frame clearing. Five rendered frames round-trip byte-for-byte through the existing RLE32 encoder/decoder. The Python suite passes 215 tests. QNX ARM build succeeds. Host 32/64-bit suite results accompany the evidence archive.

## Remaining app work

Automatic factory-navigation takeover is not solved by this UX change. The working live path still uses the Mac runner and explicit stopped-guidance confirmation; the cooperative yield is not an automatic factory signal. The QNX renderer builds, but a head-unit-only standalone service is not complete. Do not enable autostart or claim safe simultaneous factory navigation. The successful symbol-free double-buffer path and cleanup are unchanged.
