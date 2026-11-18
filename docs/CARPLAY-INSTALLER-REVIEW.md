# CarPlay Advanced Installer review — 18 November 2026

Read-only source review; no APK, payload library, installer or probe executed. V1 and vehicle files unchanged. No upstream implementation copied into this project.

## Sources pinned for reproducibility

- [ghackt/Carplay-advanced-installer](https://github.com/ghackt/Carplay-advanced-installer/tree/8df8ab72fced3101066f4ac83cbf32d1e070a209), commit `8df8ab72fced3101066f4ac83cbf32d1e070a209`.
- The installer names [st1ng/nbtevo-carplay-advanced](https://github.com/st1ng/nbtevo-carplay-advanced/tree/9a80636b5d8c6eee259105a5e9311b912935a9c7) as its actual payload. Reviewed commit `9a80636b5d8c6eee259105a5e9311b912935a9c7`, especially README, src/kombi.h, src/rgkombi.cpp, src/probe.cpp, src/rgview.h, src/rghud.cpp and src/hud.h.

## What it establishes for our investigation

The wrapper repository contains an Android installer, packaged releases and documentation. The implementation clues are upstream. Its Ethernet KOMBI path ports the same NBT-AAD J29 guidance-model stack already reviewed here: B006 on the cluster, captured factory graph, maneuver/distance/text/lane updates. Its custom polygon artwork and automatic HUD picture-box fitting belong to the separate MOST HUDTerminal path. Those features do not establish that the Supra accepts the same drawing or sizing commands.

No PiP descriptor image upload, native-window 1056 control or larger arbitrary Ethernet canvas was found in the reviewed code. The upstream Ethernet `Client::probe` only connects to the guidance TCP port and closes it; it is not a resolution/capability query. The advertised hud-probe workflow also includes test drawings, so it is not a read-only substitute for our capture plan.

The wrapper README reports a J29/A90 vehicle test. Upstream README at the pinned revision still marks its Ethernet implementation untested in-car. Preserve those as different authors' claims; neither establishes custom PiP rendering on our firmware. The wrapper also describes ID5-targeted installation behavior with limited ID6 verification. No compatibility or installation recommendation follows from this review.

## Useful changes to our batch

Upstream `src/rgkombi.cpp` contains an actual route watcher using system-log events and matching route identifiers. Its comment attributes the observed event pattern to a J29: new route guidance can be followed by a disable for the old preview route. Consequently, route start/stop attribution must correlate the visible route ID and account for backlog. A stale header comment in `src/kombi.h` says navigation yield is absent; the reviewed implementation in `src/rgkombi.cpp` contains the watcher, so the header alone is not authoritative.

We added bounded-result, non-following `sloginfo` snapshots to each phase of our own read-only collector. This supports correlation of packet, session/window and owner-observed transitions. It does not replace the working V1 navigation hook, prove that desired debug messages are enabled, or make cached log lines live evidence. No external code was copied.

The source also reinforces that longer street text clips in the windshield and that whole-graph redraws can blink. Those are useful constraints on navigation-model presentation, not evidence of a larger pixel surface. Keep the existing smooth double-buffer tach update unchanged.

## Result

This review improves the capture batch but does not unlock a larger HUD area. Continue targeting the native PiP window and its compositor/output routing. The next session should gather the planned phases and logs together, with explicit missing-evidence reporting before unplugging.
