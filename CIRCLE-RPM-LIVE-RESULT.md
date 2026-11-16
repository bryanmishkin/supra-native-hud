
## Circle candidate and live RPM results — 16 November 2026

Read-only RPM sampling passed: 40/40 valid responses, 963.0–988.5 RPM, median973.25 RPM, maximum request-to-response latency27ms. Bryan independently reported approximately1000 RPM at idle. This corroborates the read stream at idle; it does not validate all engine speeds or a continuous live HUD loop. Raw requests/replies and monotonic timing are saved in rpm.jsonl.

Circle removal did not succeed. The no-detail candidate (remove detailed-roundabout setup/reference, keep direction14) produced no visible tachometer. After normal-display confirmation, road-only (same omission, direction8) produced visible3500 with the same circle. These observations rule out treating either candidate as a circle-removal fix. They do not prove which cluster-side condition generates the symbol, or whether retained model state contributes. No additional speculative mutations were attempted.

Both runs recorded31 requests each, seven acknowledged graph-cleanup steps, acknowledged bitmap disposal, negative post-disposal resource checks and canceled local forwards. No create/dispose-instance commands were sent. Bryan confirmed both displays returned normal after each test, factory navigation worked in both displays, and final radio/iDrive/normal HUD checks passed with all test graphics gone.

Direct QNX hu-omap ARM identity verified; Mac ENET address169.254.130.200. SSH was already available and no activation utility was run this session. Local SSH master closed after checks; vehicle SSH was not explicitly disabled. User told they could unplug after all checks.

Evidence: circle-rpm-live-2026-11-16, including rpm-summary.json, verification.json, access.txt, both raw packet sets and result journals. Executed code2644fcc. Next offline work: inspect why the road-icon graph retains the circle, preserve the known control, and integrate measured RPM timing with a continuous drawing lifecycle that can withdraw stale data. Automatic factory-navigation coexistence remains unproven.

