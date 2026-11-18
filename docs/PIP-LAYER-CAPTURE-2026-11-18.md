# Targeted LayerManager capture — 18 November 2026

The missing-component capture is complete. The owner was parked with ENET connected, iDrive awake and, as subsequently clarified, the engine running. Temporary SSH was enabled using the previously approved utility. All subsequent head-unit work was read-only. No V1 files, startup settings, layer properties or drawing resources were changed; no restart or display exercise was requested.

## Verified evidence

- **30 unique files** saved with matching double reads and locally rechecked SHA-256 values: LayerManagerService, LayerManagerControl, their dependency closure/mapped libraries, video/capture components and their dependencies, plus two video configuration files.
- **94 surface records**, **75 layer records**, direct LayerManager screen-0/screen-1 descriptions, and native Screen dpy-1/dpy-2 descriptions retained.
- Current LayerManager process/map and library inventories retained; historical PID values were not reused.
- Before/after V1 checks: **15/15 matches** to the exact installed baseline; all **five permanent fault records unchanged**.
- Final resident snapshot: worker running, available, not quarantined. Owner confirmed normal iDrive/display response. SSH master and local activation relay closed before unplug clearance.

LayerManagerService SHA-256: `8a85b61891f0f96f4927b1eccefaa5d31821c7eb9eaf317484f723ac880256b1`.

LayerManagerControl SHA-256: `aa20aee1c8317668d32e919e59f7afd0430dc254f4a9c176ffca3511595832cd`.

## Immediate routing finding

LayerManager surface **1056 / 0x420** exists, but its original size, source/destination regions and virtual viewport are all zero. Native surface is `0xffffffff`; frame/draw/update counters are zero; no layer is listed. Its visibility flag is 1, which alone does not make a drawable or displayed image. This supports distinguishing a registered surface placeholder from the actual previously captured 800×480 native window.

Direct LayerManager screen 0 is 1280×480 with a populated layer render order. Screen 1 is 800×480 with an empty layer order. Two enumerated layers (`0x80090000`, `0x800c0000`) are absent from both recorded screen orders. No layer routing was modified.

The newly discovered `/opt/sys/etc/ethervideo.cfg` selects `/dev/icam2`, an H.264 decoder and a display window. This configuration describes an **incoming decoded video path**, not by itself the outgoing PiP transport we need. It and `videocapture_hu.cfg` were retained with associated binaries so this can be investigated offline rather than requiring another generic capture.

## Capture issues resolved without V1 changes

The first surface query could not load `libilmClient.cpp-ne.so.1`. Re-running the same read-only query with command-scoped `LD_LIBRARY_PATH=/opt/sys/lib:/lib:/boot/lib` succeeded. This changed only that command's environment, not system configuration.

The process-map tool left-truncates long library names. Its `graphics.cpp-ne.so` and `nication.cpp-ne.so` entries uniquely match the fully named, independently downloaded ELF dependencies `libcommunication_graphics.cpp-ne.so` and `libcommunication.cpp-ne.so`. They were not genuinely missing libraries. The collector now records unique suffix resolutions explicitly.

`get scene` and the on-screen footer of layer queries produced a spurious screen ID and errors. Those raw errors remain in the evidence. Direct screen 0 and 1 queries succeeded, supplying render-order membership independently; native Screen display metadata was also saved. Individual layer properties were retained, but the erroneous footer must not be cited as a valid screen association. Original incomplete collector manifests remain unchanged; `SESSION-RESULT.json` records how each issue was resolved.

## Next offline work

Trace the captured LayerManager implementation, especially native-surface association and forwarding, against surface 1056's placeholder state. Follow the PiP disposal observer through its transport callback. This capture fills the previously named missing-component gap; it does **not** establish that a larger V2 drawing surface is available or that an executable expansion test is ready.

Public repository contains findings and collector improvements only. OEM binaries, private installed-state evidence and raw captures are archived in Drive. Collector offline-plan execution and all 12 existing consolidated-capture regression tests pass; this session supplies the actual read-only live evidence.
