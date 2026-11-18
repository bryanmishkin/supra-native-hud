# PiP marker car result — 18 November 2026

**Larger image not visible. V1 restored and verified.** The owner saw only a factory right-turn arrow in the windshield, not the white border/cross or colored corners. The initial “windshield only” answer was explicitly clarified; it must not be counted as a successful custom image.

Candidate source: `2e2008e1b06807b96234bde782f4e98d882f81ce`, [30-second experiment](PIP-MARKER-TEST.md). Native Screen implementation credited to **ryseek**, with **Sq00ky / nanaisu and the Supra Android Auto contributors**; [notices](../THIRD_PARTY_NOTICES.md). Reference vehicle parked outdoors, engine running, guidance and radio closed. No persistent V1 components or configuration changed.

## Machine evidence

| Stage | Result |
|---|---|
| Baseline and pause | All 13 packaged V1 files plus two active startup configurations matched. Cooperative CLEAN stop, STOPPED resident and absent worker/broker sockets verified. Owner confirmed normal displays. |
| Admission | Secondary OTHER2 output was 800×480 with empty scene/no windows. Surface 9001 did not exist. Candidate readbacks matched the exact kit; no-argument loader check passed. |
| PiP resource | Slot `0x02000004` checked absent, configured as 320×200/type 2/depth 1/packing 0, then checked present. No factory instance create/dispose or other resource writes. |
| Native output | First post reported display index 1, pipeline 2, stride 3200, window ID 268444457, maneuver metadata and no red/blue swap. Producer posted **255 frames** in its bounded run and reported successful local cleanup. |
| Guidance | 20 request/reply transactions total, including resource checks/configuration, graph setup and cleanup. No rejected transaction was reported. The right-turn arrow confirms some navigation model became visible; it does not prove PiP pixel delivery. |
| Removal | All seven withdrawal/dispose operations acknowledged; selected PiP resource checked absent. Native display scene/windows were empty. Owner confirmed arrow gone and both displays normal. |
| LayerManager | After native window destruction, surface 9001 remained as an invisible, unbound placeholder: zero-sized source/viewport, native surface `0xffffffff`, no layer, zero frame/draw/update counters. This was not a live image. The normal restart removed the placeholder entirely. |
| V1 return | Owner restarted iDrive and confirmed V1 visible/updating. Final verification again passed all 15 file/config comparisons, hook presence, heartbeat and RPM advancement, worker running and no quarantine. Test RAM directory and surface were absent; permanent fault records were byte-identical to preflight. SSH master closed. |

The secondary display counter changed from 1 before the test to 258 afterward; it returned to 1 after restart. This corroborates native display activity, not physical windshield pixels or a receiver binding.

## Recording integrity

Two overlapping passive, non-promiscuous 120-second recordings were retained:

- Direct SSH-streamed capture: **4,781 packets**, 1,030,290 bytes, 120.005 seconds, zero kernel/interface drops; SHA-256 `58b0f0497cc03558719dc82d2031a2c5a8b0fbfbf26b545add0e348df531e893`.
- On-unit capture: **4,782 packets**, 1,030,741 bytes, 120.006 seconds, zero kernel/interface drops; SHA-256 `6af6f73d3c6b2d26ee4e940e2408a9305fc69cbbbf1202375ed848a2d68245c3`. Retrieved twice with identical bytes and successful recorder exit.

The first launch used a remote background shell whose local SSH wait timed out after 50 seconds; its recorder nevertheless completed normally. A separate foreground SSH stream supplied the primary recording. Future sessions should use a local asynchronous SSH process for the foreground recorder, not a short-timeout remote background launcher.

Both captures passed bounded TCP extraction with no reported parse errors. The primary capture contains 20 TCP directions. **No B009 messages were observed in either interval.** That does not establish the receiver's pre-existing sink state; absence of a switch event is not proof that HUD selection was inactive. Raw captures remain private in Drive.

## What this resolves and what it does not

The separate native producer loads, posts to the expected secondary output, and tears down on this Supra. The PiP configuration and detailed navigation model are accepted, and the tested resource can be removed with an absence check. The owner-confirmed visible result is still only the factory arrow.

The remaining failure lies between accepted native output/resource metadata and visible PiP content. The captured evidence does not distinguish metadata identity/channel convention, packaging, detailed-model activation, or physical receiver routing. Do not change the report into “windshield PiP works,” infer that a new DisplaySink switch was mandatory, or replay the same candidate as though it were a verified V2 renderer. Continue comparison with ryseek's captured frame convention and the retained Supra controller/output-driver evidence offline.
