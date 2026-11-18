# Output-driver batch — 18 November 2026

Completed on the reference Supra while parked, engine running, ENET connected. V1 remained installed and running. Temporary SSH was enabled using the previously authorized utility; the capture itself used read-only commands. No restart, drawing, startup change or V1 pause was performed. SSH master was closed after verification.

## Captured and verified

65 unique remote files were locally hash-verified. Static transfers used matching double reads or fresh remote verification of cached content. Captured all graphics-directory configurations and libraries, WFD and Vivante drivers, screen executable and startup script, boot script, loaded dependency closure, current process maps/arguments, display and blitter descriptors, LayerManager screen 0/1 and surface 1056, interfaces/routes, and relevant screen environment settings.

The first collector stopped on QNX `ls -1` returning literal `.` and `..`; the local parser now ignores only those exact directory entries and still rejects traversal/shell characters. The resumed main batch reported three truncated map names. Follow-up captured their actual files and dependencies:

| Truncated map name | Verified full path |
| --- | --- |
| ante-omap5430.so.1 | /lib/libGAL-vivante-omap5430.so.1 |
| ibinputevents.so.1 | /lib/libinputevents.so.1 |
| ivante-omap5430.so | /lib/screen-vivante-omap5430.so |

Also captured `/lib/libextproc.so`, referenced by graphics configuration, and `/lib/libcapture-soc-omap4-5.so`, referenced by the startup script. The original incomplete manifest is retained as evidence; private `COMPLETION.json` joins the follow-up and final checks. No required files remain unresolved for this batch. Optional path probes and the absent runtime `resident.status` file are recorded, not silently treated as present.

## Direct findings

- `GRAPHICS_ROOT=/lib/graphics/omap5430`, `CID_DISPLAY_RES=02`, `RSE_DISPLAY_RES=01`.
- `graphics.conf` selects the captured 1280×480 configuration. `start_screen.sh` documents coding-dependent selection and then executes screen. It was read, never executed by the collector.
- WFD configuration binds gfx/video1 to display 1 and video2/video3 to display 2.
- Native display 1 reports HDMI1, 1280×480 at 60 Hz, Vivante composition loaded, and two attached windows.
- Native display 2 reports OTHER2, 800×480 at 60 Hz, Vivante composition loaded, with empty scene and no attached windows.
- Configuration comments call the second display OTHER1, while the live descriptor says OTHER2. Preserve that discrepancy; do not rename either as windshield evidence.
- The captured WFD library is the OMAP5430 output driver. Its configuration libraries refer to local I2C/HDMI interfaces. This is a starting point for binary tracing, not proof that PiP pixels reach the cluster.

## V1 preservation

All 13 installed baseline components and both live startup configurations matched the published V1 baseline before and after the batch. The final acceptance snapshot reports worker running, available true, quarantined false; worker starts remained 2 and clean stops remained 1 between first and final snapshots. All five permanent fault records were unchanged. The owner confirmed V1 updating normally and iDrive/both factory displays normal. No larger drawing test was performed.

## Next offline work

Trace captured screen/WFD/Vivante configuration and driver paths against the earlier HMI texture and 21×1 PiP metadata evidence. Establish the actual output and receiver binding before proposing a larger-display test. An empty second output is not proof of available windshield space. No additional vehicle exercise is justified merely to repeat this file capture.

Collector regression checks: 5 output-driver tests and 12 bounded-transfer tests passed after the QNX listing adjustment. Runtime sources and installed V1 were unchanged. Raw OEM files and private baseline content remain outside GitHub; Drive holds the hashed private archive.
