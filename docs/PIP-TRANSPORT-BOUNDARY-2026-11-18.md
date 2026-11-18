# PiP transport and removal boundary — 18 November 2026

Continues [session binding](PIP-SESSION-BINDING-2026-11-18.md). V1 is unchanged. A larger drawing test remains unproven; this report identifies a specific uncaptured component rather than recommending another general radio/navigation capture.

## Native window routing reaches a missing component

NavigationFully `0x882e94..0x883158` creates its native window through the KD API. It applies size, caption, QNX class and QNX ID-string properties. Caption, class and ID string all come from the `WindowCaption` option; `ScreenNumber` is optional and is applied only when nonzero. This path does not itself open a network pixel stream.

The retained live metadata identifies **PID 159773, `/opt/sys/bin/LayerManagerService`**, as the window manager. Window 1056's downstream composition therefore warrants investigation in that component. This is an identified local window manager, **not proof it exports windshield pixels**. It may only manage local displays.

Neither LayerManagerService nor LayerManagerControl was found as a saved standalone file in the project evidence, Documents or Downloads search. Archives not already expanded were not exhaustively searched. The earlier capture collected navigation and graphics libraries, not the layer-manager executable.

A locally retained external reference (`Sq00ky/Supra-iDrive6-Android-Auto`, local checkout revision `87fd9624f33f7ec02d812ebec02a416a3875a320`, `milestone-7/src/video_manager.cpp`) describes numeric Screen window IDs becoming LayerManager surfaces on first post, and uses `LayerManagerControl get surface <id>`. That code concerns center-display Android Auto/CarPlay surfaces, not a proven HUD route. It supports a read-only surface lookup, not borrowing its write/visibility operations for the windshield.

The saved HmiMain3D was also checked (SHA-256 `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`). It contains RIC PiP types and peer-window machinery, but the bounded string/reference review did not establish the missing native-window pixel export. Shared type names are not transport evidence.

## PiP resource removal is reference-counted

The controller's PiP-specific `removeResource` implementation is `0xa54d1c`:

- Validate the resource ID, resolve its vector entry, decrement the reference count at entry offset `0x0c`.
- If the count remains nonzero, do not destroy the entry.
- At zero, return non-sentinel HMI and IC IDs to their respective available-ID vectors (`0xa663f8`, `0xa66378`), destroy the local entry and clear the vector slot.
- Caller branch `0xa3ae20..0xa3ae40` checks the true-removal result and then invokes `0xa34ad4`, identified by its diagnostic as **notifyDisposeResourceToComm**. It supplies distinct HMI and IC resource IDs, stores them in notification state and invokes observers.

This adds a concrete disposal-notification edge beyond the previously traced navigation-job cancellation. It does not yet prove the observer's complete request/ACK ordering, pixel-stream termination, or receiver-visible disappearance. The existing B006 method-8 resource disposal schema is known, but no PiP-specific live disposal was captured. Do not delete factory IDs or interpret the local reference count as app ownership.

## Exact next evidence, with no display exercise

`tools/collect_pip_router.py` prepares a narrowly scoped **read-only** download:

- Exact layer-manager executable and control utility paths; double-read and SHA-256 verification.
- Current process list and layer-manager memory map, using the current PID rather than historical PID 159773.
- Read-only `get surface 1056` output, with command failure recorded explicitly.
- Mapped-library candidates plus transitive ELF dependencies from fixed existing library directories, with bounded transfers and unresolved names reported.

Default invocation prints its plan and performs no network operation:

```sh
python3 tools/collect_pip_router.py
```

It uses the same verified address/known-host/socket arguments as the existing collectors and requires explicit `--execute`. The environment needs pyelftools. No engine start, driving, guidance action, restart, drawing, layer-property write or V1 modification is part of this capture. The head unit must be awake and approved diagnostic access available. This is a missing-component transfer, **not** an executable larger-display test.

Offline validation: plan invocation succeeded; dependency-name/architecture extraction succeeded against both retained controller and HmiMain3D ELFs (21 and 56 direct dependency entries respectively). The 12 existing consolidated-collector regression tests also passed. Live utility availability and transfer success remain untested. A complete transfer never sets pixel transport or drawing readiness to proven.

## Decision

The descriptor, content identity and native producer are traced, and resource-removal notification is now located. The actual windshield pixel-export edge is still absent. The identified next component is not available locally, so an actual larger-display test cannot honestly be completed from the current evidence. Collect this bounded component bundle when access is next available, then trace the implementation before deciding whether another live display experiment is warranted. Do not change V1 or enlarge its bitmap as a substitute.
