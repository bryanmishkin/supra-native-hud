# Ready next-trip batch — full HUD surface activation

Two prepared tests, 30 seconds each. This is the unrun A102 batch, not another road-icon upload, strip-width test or Hz test. The goal is to establish whether the installed008 windshield receiver activates the larger TestBmp surface traced in004. Arbitrary uploaded-image access remains a separate, unfinished integration.

Use the exact commands and preflight in [the diagnostic-surface procedure](HUD-DIAGNOSTIC-SURFACE-TEST-2026-11-20.md). Keep the car parked, ignition state stable, navigation stopped and radio selector closed. Cooperatively pause V1; verify all15 preserved installed files and STOPPED state. No installation or firmware patch is part of this batch.

| Order | What runs | What it answers | Record separately for windshield and cluster |
|---|---|---|---|
|1|Dim solid RGB, selector0|Does the separate full-size node activate at all, and is its physical height greater than the familiar strip?|Visible/absent; position; width and height relative to normal HUD speed text; photograph showing both pattern and speed text|
|2|Factory grid and circles, selector0x5c|Does the bitmap path occupy the same taller region, and are its edges/circles visible?|Visible/absent; grid/circles vs substituted symbol; upper/lower/left/right edges; apparent crop; photograph with speed text|

Before each start, the runner requires the exact recorded ECU identity, a positive stop acknowledgement, a verified V1 file capture and a live stopped-state check. Announce the viewing window only after start acknowledgement. Run one case at a time. Require stop acknowledgement AND owner-observed normal displays after each case; do not infer visual cleanup from the acknowledgement. Any rejection or uncleared pattern ends the batch. Do not change session, unlock, reset or substitute another routine.

After both cases, compare a fresh15-file capture with the pre-capture. Restore V1 only through the established recovery procedure when requested; distinguish preserved files from a running worker. No claim of a successful larger canvas is permitted from an ACK alone, from seeing all markers, or from a cluster-only result.

The car decision is deliberately diagnostic: solid and grid both taller supports the full-size rendering route; solid taller but grid absent isolates bitmap asset access; either showing only the strip means the full-size projection hypothesis failed on installed008. These observations determine whether future uploaded-image binding should target this surface. None alone proves that Ethernet-uploaded pixels reach it.

Offline readiness checks completed20 November: seven native request/cleanup/negative cases; 256 native renderer selector cases plus record copy/withdrawal; ten host runner tests; the 408×132 image/cache/geometry checks and native named-asset cache lookup/removal. No car connection was made during preparation.
