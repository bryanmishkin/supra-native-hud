# Sport HUD live result / v1 UI candidate — 16 November 2026

The new larger-digit sport layout passed live testing on the Supra windshield HUD. Bryan confirmed readability, smooth updates, no clipping and no unwanted circle or arrow. The initial color test showed blue shift lights. Swapping red and blue once at the display boundary corrected the projection: one orange light at simulated5500, three orange/one red at6200, and five red at6500 were visually confirmed.

## Exact tested profile

Use `--renderer-style sport --swap-red-blue --graph-variant empty-direction-zero --double-buffer` with the existing measured-RPM runner, explicit stopped-guidance confirmation and verified current connection arguments. The native renderer keeps canonical BGRA for correct offline previews. The correction applies before RLE encoding in both static and live paths; the reverse-engineered compressor remains unchanged. This is evidence for this Supra road-icon path, not a universal QNX color convention.

## Live evidence

Eight bounded runs: original30-second live UI, original5500/6200/6500 color sequence, corrected6500 red probe, corrected5500/6200 sequence and corrected30-second live UI. All eight acknowledged all seven graph-withdrawal steps, disposed tracked bitmaps, checked them absent, preserved the shared factory instance and canceled local forwards.

Original live run:120/120 valid RPM readings,634–6542 RPM,maximum32ms read latency,sample span29.937seconds. Corrected final run:120/120 valid readings,632–6889 RPM,maximum29ms latency,sample span29.919seconds. Both completed their30-second display windows. Although idle was requested, captured RPM was not confined to idle; preserve those measured ranges rather than reporting an idle-only test. The static color tests used simulated displayed RPM and did not command engine speed.

Final user confirmation: “Readable and smooth throughout; no flashing or symbols.” Then “Yes, both displays normal; test graphics gone.” Factory navigation worked normally in both displays. Final radio/iDrive/HUD check: “Yes, everything normal; test graphics gone.”

## Session and validation

ENET en8 active100baseTX/full-duplex,Mac169.254.175.40. Temporary SSH had closed; restarting the previously verified Bavarian utility restored it, with the known relay-tag warning. Saved host-key checks passed and direct QNX hu-omap6.5 ARM identity matched. Local SSH master closed after testing; vehicle SSH was not explicitly disabled. Nothing installed, no startup configuration changed.

The color fix passes217 Python tests, including channel/alpha preservation, inverse mapping and RLE round-trip. Existing native/QNX sport-renderer build is unchanged by this transport-side correction. Raw requests/replies, RPM timestamps, exact user observations, original blue result and corrected results are in sport-live-2026-11-16.

## v1 release boundary

Bryan requested shipping this as v1. This is a verified v1 UI candidate, not yet a standalone head-unit deployment. Current live RPM transport, display lifecycle and navigation-yield request run on the Mac. Automatic factory-navigation arbitration, standalone head-unit runtime and reliable behavior across process/connection failure remain incomplete. Factory navigation was tested after full withdrawal, not concurrently. Do not describe the successful post-cleanup navigation test as automatic coexistence. Demonstration scale7000 and shift cue6500 remain illustrative rather than validated vehicle limits.
