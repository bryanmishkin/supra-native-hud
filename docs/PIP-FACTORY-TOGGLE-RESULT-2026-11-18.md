# Factory HUD navigation toggle: live result

The owner found the normal HUD settings: Navigation, Entertainment/phone and Vehicle messages. Navigation was originally checked. With factory guidance active, unchecking Navigation removed the windshield instruction; checking it again restored the instruction. The owner additionally reported that turning Navigation off also removed the tachometer. Treat these as human observations, not packet-decoded visibility measurements.

That is consistent with a common windshield visibility control for navigation and the current tachometer, which uses the guidance renderer. It does not establish a PiP pixel route or a larger surface. Do not call this a successful larger-display test.

## Evidence saved privately

Two bounded 120-second recordings, 4,918 and 12,209 packets respectively, zero capture/interface drops, valid streams and verified recorder process/file cleanup. Packet hashes:

- First: `e6fbdf5f322e4481e4b9f6ce8d06fd8fbc2d32e21b5c1adb2089cb6ddb277114`.
- Second: see the private recording result and archive manifest.

The known-shape TCP binding decoder produced no DisplaySink/native-image/high-guidance-binding events and no decoder errors in either recording. This is not proof of no routing traffic: unknown formats, UDP and other transports require separate analysis. Full packets are retained.

Surface 1056 and LayerManager screen 0/1 snapshots were byte-identical across original, navigation-off and navigation-on. Native display 2 was also unchanged. Native display 1 differed; its exact descriptor difference remains to be interpreted and must not be labeled a routing change without analysis.

## Capture limitations discovered

The first 120-second window ended before the navigation-on phase snapshot was recorded. The restored/on state was captured in a second window. This was not the planned uninterrupted four-phase acceptance run, and exact on-transition coverage must not be assumed. The second on-to-restored marker spacing was shorter than the planned 30 seconds, although both represent the same restored checked setting. No completed four-phase audit is claimed.

QNX `date +%s` returned literal `%s`; the recorder's original epoch alignment is invalid. A separate bounded `date -u '+%Y-%m-%d %H:%M:%S'` sample was saved, with host before/after timestamps. Use that sample and its one-second precision when analyzing packet timing. Do not silently replace original evidence fields.

## V1 preservation and exit

All 15 before/after installed comparisons passed. Permanent fault files were unchanged. No V1 startup/component changes, custom producer, synthetic images, layer setters or new SD subscription were used. Navigation was restored checked. Owner stopped guidance and confirmed V1 returned and updated normally. Both temporary RAM recorders were removed. The owner was told it was safe to unplug after those checks.

No author contacted. Continue with offline raw-traffic and descriptor analysis; do not repeat the failed arrow marker or present this checkbox as an established PiP selector.

## Same-session height rectangle follow-up

Owner additionally identified a rectangle around the HUD area when opening Height. It disappears after a few seconds. With a third recorder running, the owner reopened Height without changing the adjustment and confirmed appearance/disappearance. This recording saved 20,676 packets over 120 seconds, zero drops and verified cleanup; SHA256 `b58293c8bc7a112830d5623a5cf9b9e929d959b62138d1b629e1b4ca96ad01f1`.

The trace contains real V1 B006 bitmap uploads and updates (slots 8/9), demonstrating that this recorder can observe current drawing traffic. Initial known-shape analysis still finds no DisplaySink/native PiP binding. The rectangle may be a receiver-generated alignment overlay; that remains an inference, not an established pixel path. The snapshots were taken after the rectangle disappeared, not during its visible interval.

The display-1 difference from the checkbox experiment is only its `counter` field (2125 to 2220), not a changed viewport/geometry. A suspected VLAN-filter exclusion was investigated but not confirmed: the retrieved resident startup trace contained 10,583 untagged IPv4 Ethernet records, and the third recording sees V1 drawing. Do not attribute the missing PiP binding to VLAN filtering on this evidence.

Owner also reports the entertainment/radio setting can remove/re-add those controls. No additional radio-toggle test was performed. Final owner check: rectangle gone, V1 normal, Navigation checked. Final installed hashes match and permanent fault records remain unchanged. The larger-image routing question is still unresolved; this session did not demonstrate a custom larger pixel surface.
