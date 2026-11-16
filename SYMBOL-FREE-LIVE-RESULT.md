# Symbol-free smooth RPM and navigation yield — 16 November 2026

The parked test now shows measured RPM and the bar smoothly, without the unwanted circle or arrow. The successful combination is `--graph-variant empty-direction-zero --double-buffer`: explicitly empty the selected high-guiding union (tag0), keep the coming-road bitmap reference, set maneuver direction0 and alternate bitmap slots without repopulating the high-guiding model.

This is a live-verified combination for the captured Supra configuration, not a universal interpretation of direction0 or a guarantee for other firmware. The prior empty-detail/direction8 candidate showed3500 with a turn arrow. Changing only direction8 to0 then showed3500 and the bar without either symbol. The user confirmed “NO Circle”, “Or arrow”, and “3500 and the bar”.

## Full live verification

After the static proof, a measured-RPM run showed smooth symbol-free drawing but ended early at7002 RPM because the demo renderer rejected values above7000. All cleanup checks passed. The renderer's input guard was corrected to7700, matching HudCore's already-existing maxRpm×1.1 acceptance range for the illustrative7000 scale. This is a display-input guard, not an engine operating limit or an instruction to rev. Boundary checks accept7002/7700 and reject7701, NaN and negative input.

The repeat completed the full30-second observation window at idle:120/120 valid readings,648.5–672.5 RPM, maximum read latency31ms, sample span29.974seconds,120 uploads and746 recorded requests. The user confirmed: “Smooth throughout, no circle/arrow; both displays normal now.” Subsequent factory navigation in both displays, radio selector, iDrive and normal HUD all passed, with test graphics gone.

## Navigation-yield result earlier in this session

The existing smooth control ran for about10seconds, then an explicit local navigation-yield request stopped it.42 valid readings were captured,41 images uploaded and312 requests saved. `navigation-handoff.json` reported protocol_ready:true only after cleanup. The user clarified that the circle was present during that control run but both circle and RPM numbers were gone afterward. Factory navigation then worked in both displays, followed by normal radio/iDrive checks.

This establishes cooperative withdrawal before starting navigation. It does not establish automatic detection, simultaneous factory navigation/tachometer coexistence, or a live yield trial specifically using the later direction0 combination. That combination's normal timed cleanup and subsequent factory navigation were separately verified.

## Cleanup and preserved evidence

All five runs in this continued session (arrow candidate, control yield, symbol-free static, early renderer-limit stop and complete symbol-free live run) acknowledged all graph cleanup steps, removed tracked resources, checked them absent and canceled local forwards. No factory instance was created/disposed. The user confirmed normal displays after each relevant trial and factory functions after the final run. The local SSH master was closed; vehicle SSH was not explicitly disabled.

Private evidence folders: `smooth-yield-live-2026-11-16` and `symbol-zero-live-2026-11-16`. They retain raw packets, RPM timestamps/replies, handoff result, the early failure and exact visual observations. The original control remains unchanged as a diagnostic baseline; explicitly select empty-direction-zero for symbol-free experiments.

Remaining production work includes navigation ownership/arbitration, transport-failure expiry guarantees, validated operating thresholds and driving validation. This result is bounded parked testing, not an installed production app.
