
## Live tachometer windshield test passed — 16 November 2026

Ran the prepared synthetic 1000 → 3500 → 6500 RPM sequence while parked outdoors. Bryan confirmed the numbers and bar changed in the windshield. He did not observe the gauge cluster during the tachometer windows, so tachometer visibility there is unverified for this run. The built-in circle accompanied the drawing, as expected from the unchanged navigation support graph. This is stepped synthetic data, not measured engine RPM or continuous refresh.

All three complete lifecycles succeeded: 32 requests each (96 total), seven acknowledged graph-cleanup steps per frame, bitmap disposal acknowledged, post-disposal bitmap absent, and temporary forward canceled. No create-instance or dispose-instance request was sent; the shared factory instance was preserved. Bryan confirmed both displays returned to normal with no test graphics. He then started factory guidance and confirmed normal navigation in both displays, and finally confirmed radio selector, iDrive and normal HUD worked normally after guidance stopped.

Windshield drawing, repeated full-cycle resource reuse, removal, and staged factory-navigation restoration are verified. Per-gap visual removal and individual shift-light correctness were not separately reported. Continuous refresh, live RPM integration, circle removal, automatic factory-navigation coexistence and independent ownership are not established. No firmware/coding installation was performed.

ENET en8 was active at 100baseTX full duplex, Mac 169.254.206.76. Temporary SSH was restored using the previously verified utility; the direct QNX hu-omap ARM identity was verified. Local SSH master was closed after testing; vehicle SSH was not explicitly disabled.

Evidence: tachometer-live-2026-11-16/run-01 contains each frame's request/reply packets and result journal; protocol-verification.json records all cleanup checks; visual-verification.json preserves the user's exact confirmations and unobserved scope. Executed source commit: 0389627b760ceaedf4373540c7893feddaedb9ea.

