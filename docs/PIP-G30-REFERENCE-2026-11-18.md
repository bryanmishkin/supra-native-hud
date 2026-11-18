# Native PiP implementation reference — 18 November 2026

Credit to **ryseek** for the G30 PiP implementation, building on **Sq00ky / nanaisu and the Supra Android Auto contributors**. Reviewed [PR #232](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/pull/232), pinned [source a0242e1](https://github.com/ryseek/Supra-iDrive6-Android-Auto/tree/a0242e1c30d17b138845c18d6bf86ae0cd99ead6), and [issue #226](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/issues/226). See [attribution and license requirements](../THIRD_PARTY_NOTICES.md). This update incorporates no external implementation code.

This branch was not part of the earlier main/J29 source review. It provides a concrete native pixel producer and materially narrows the transport investigation. It does **not** establish a working Supra windshield implementation. V1 runtime, baseline, startup and tags remain unchanged. No car connection was made for this review.

## What the implementation actually does

All source paths below are under `milestone-7/src/cluster/` at the pinned revision.

| Stage | Source evidence | Consequence for our work |
|---|---|---|
| Native output | `video/native/native_screen.hpp`: private Screen window, display index 1, 800×480 backing, double buffers, format 8, usage 6, source transparency; pixel memory obtained from Screen | A static marker does not need Android Auto, H.264 or the decoder. The native Screen producer is the relevant component. |
| Frame envelope | `profiles/g30.hpp`: 84-byte metadata; picture counter in bytes 0–1; templates distinguish map/maneuver. `native_screen.hpp` reserves row 0 and starts visible content at row 1 | Our traced metadata block has a real producer-side analogue. Its final BGRA template must not be equated directly with our CPU-upload byte rotation. |
| Visible image | G30 content is 620×313 within the 800×480 backing; Screen source/window sizes stay 800×480 | Backing size, visible sink size and protocol resource dimensions are distinct. The driver's packed width is not additional HUD space. |
| Receiver registration | `video/native/native_methods.inc`: resource `0x02000000`, method 3, variant 3/type 2, 800×480, color-depth 0, packaging 1; binds resource into detailed maneuver's high-guidance field | Pixels are not appended to the resource descriptor. Guidance selects the resource while Screen supplies the native output. |
| Sink handshake | `video/native/control.hpp`: B009 event, scale/width/height/selection; completion echoes selection. G30 cluster is 620×313/1, HUD is 277×160/0 | The source recognizes HUD separately and pauses cluster video on that destination. Removing that condition is not a justified Supra port. |
| Cleanup | Drains an outstanding response, then sends acknowledged cancellation graph with a shared deadline; unsubscribes on full stop. Screen teardown hides/destroys its own window | Local window destruction and acknowledged graph cancellation are separate. This is not proof of individual remote PiP resource disposal or our own resource ownership. |

The profile selector rejects video builds without the G30 selection. The documented default J29 build retains turn guidance rather than enabling native PiP. The G30 producer also uses a temporary producer address (`160.48.199.120`); that is not an existing Supra address we may assume is free or required.

## Comparison with retained Supra evidence

Our captured secondary Screen display is 800×480, consistent with the candidate backing. Captured output-driver execution establishes a port-2 native path with RGBA-over-RGB packing. Together these make secondary Screen output a concrete transport candidate, rather than an unspecified Ethernet image upload.

However, the retained Supra B009 body is `3ff000000000000001cc00ed01`: scale 1.0, 460×237, selection 1. It matches **neither** G30 sink tuple. Correction from the retained target trace: [SESSION-CONTRACT.md](../SESSION-CONTRACT.md) already resolves selection 0 as HUD and 1 as Kombi in the Supra controller (0xa7a228..0xa7a2d4). This agrees with the G30 labels. It does not establish HUD dimensions or a client-callable sink-selection request. Our advertised PiP configuration is 320×320, while G30 configures an 800×480 backing. Neither number alone is permission to resize the Supra resource.

The earlier metadata codec operates on the factory CPU upload; the G30 template describes captured BGRA output. Comparing their raw bytes without the intermediate format conversion would produce a misleading maneuver identity or frame counter.

## Additional retained-controller trace

Controller SHA-256: `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`.

- Sink notification at `0xa7a448` forwards to native display session virtual slot `0x24`. Constructor `0xa7b0c8` installs vtable `0x10574b0`; this slot resolves to `0xa7c5c4`.
- That handler dispatches through the task at session offset `0x20`, virtual slot `0x18`. Task constructor `0xa83ab8` installs vtable `0x1058f00`; the slot resolves to `0xa837a8` (`scheduleSinkSwitch`).
- This routine iterates existing jobs and recomputes guidance type via `0xa86b10`/`0xa8699c`. It is not itself a direct assignment to Screen display 2. The selector uses guidance-type ranges starting at 4301, 5301 and 8301. These values are not pixel dimensions or Screen IDs.
- Coding handler `0x6ddb74` calls `0x6f453c`; value 3 follows the diagnostic “ethernet IC coded, do not start MOST guiding.” This narrows the legacy MOST path only; it does not prove native video is absent.

Private bounded disassembly is archived separately; factory executable bytes are not added to GitHub.

## Next implementation target

Use this source to resolve the native frame envelope, resource-to-maneuver identity and sink selection against the existing Supra evidence. The intended experiment is a short static patterned image through an app-owned Screen window with acknowledged cancellation and V1 restoration—not a decoder installation or another general capture session.

**No larger-windshield executable is declared ready by this report.** In particular, copying G30 metadata, overwriting factory PiP resource 0, or drawing on display 2 alone would not establish windshield binding or clean removal. Keep the G30 source and its credit visible in future implementation decisions; do not repeat the earlier conclusion that reviewed J29 mainline files cover this separate branch.
