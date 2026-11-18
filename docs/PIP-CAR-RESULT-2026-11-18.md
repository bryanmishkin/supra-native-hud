# PiP investigation result — 18 November 2026

Parked outdoors, engine running. The owner authorized temporary SSH, then a passive packet recording and read-only process, window, shared-memory and system-log snapshots. V1 remained installed and running; no app/profile/startup changes, PiP allocation, custom drawing or restart was performed.

## Concrete finding

The NavigationFully process owns native window **1056**, exposed through QNX Screen metadata. Live dimensions are **800 × 480**, format RGBA8888, OpenGL ES2 usage, display ID 1. This differs from the earlier static constructor's 800 × 384 and must take precedence for this session.

Across normal HUD, radio popup, owner-confirmed windshield navigation, and final-normal snapshots, this window remained realized but reported zero updates, zero clipped visible area and zero total visibility counters. The first buffer's SHA-256 was identical before and during navigation. Both backing buffers were retained privately for offline analysis; their contents alone are not an atomic live-frame assertion.

**Interpretation:** window 1056 was not visibly composited on its assigned local display in these sampled states. Factory windshield navigation worked while it stayed inactive. This argues against treating this native window as the current windshield pixel source. It does not prove that the larger PiP capability can never be activated or that an unseen downstream path cannot exist.

## Traffic and capture verification

- One 120.01-second recording: **13,661 packets**, **zero packet/interface drops**, zero recorder-transmitted packets.
- Packet extraction and framing checks passed; recorder process absent and its temporary RAM directory cleanup verified.
- B006 resource traffic: 223 type-1/tag-2 bitmap requests and four type-3/tag-4 text requests. **No tag-3 PiP descriptor requests.** V1 was running, so its bitmap traffic is included and must not be mislabeled factory PiP output.
- Two B009 sink events and two completion messages were retained, along with B00E radio and B006 navigation traffic. No guidance-create exchange or cold startup was captured.
- All six executed phase metadata captures completed, including system-log snapshots. The owner confirmed radio visible, navigation visible in the windshield, and V1 returning after guidance stopped.

Scope limits: radio closure and guidance start were one combined owner action, so there is no separate radio-closed snapshot. The initial normal metadata precedes recorder READY; the recording contains a normal interval before radio. Navigation-stop-request metadata is inside the recording; final-normal metadata follows recording completion. Logs contain backlog and are not independent live DisplayableData sequence/length evidence. These distinctions are retained in the private session result rather than presenting seven separately verified phase captures.

## V1 preservation and final check

All **15** installed-component/startup comparisons matched the exact V1 baseline before and after. All five permanent fault records were unchanged. Final resident status reported worker running, available and not quarantined. The owner confirmed smooth V1 updates, guidance stopped, radio closed, and normal factory displays/iDrive. The owner was cleared to unplug after these checks.

## Offline next step

Use the captured native-window metadata and display descriptions to trace why the advertised PiP resource has no active local window output in this session. Compare the B009 exchanges with model updates and source-window registration. The evidence does not justify writing window 1056, borrowing factory buffers, changing coding, or enlarging V1's bitmap. No larger V2 surface is proven yet.

Private evidence includes packet capture/reassembled streams, phase manifests, log snapshots, native window/display metadata, both sampled PiP buffers, before/after V1 records and a SHA-256 inventory. OEM data and route-related contents are excluded from GitHub.

Offline follow-up: [per-connection pixel-path analysis](PIP-PIXEL-PATH-2026-11-18.md) separates all V1 bitmap uploads from factory model traffic and records the native-display and command-ring findings.
