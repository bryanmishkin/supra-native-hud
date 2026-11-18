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

## Offline follow-up: subscription is present even without a new selection event

The new `tools/audit_pip_discovery.py` decodes the known B009 UDP SD subscription/ACK shapes, separately from the TCP selection-event decoder. All three complete captures replay successfully:

| Window | TTL-3 subscriptions | TTL-3 ACK packets | TTL-zero unsubscribe |
| --- | ---: | ---: | ---: |
| Original/navigation-off | 113 | 226 | 0 |
| Restored/guidance-stop | 61 | 122 | 1 |
| Height overlay/V1 running | 0 | 0 | 0 |

Counts are packets, not a proof that each ACK corresponds to a distinct negotiation. The factory endpoint is HU `160.48.199.119:65497`; cluster SD is `.96:30490`. The unsubscribe timestamp is 1795040615.521259 on the vehicle clock, before the owner's guidance-stopped/V1-returned confirmation at host 1795040637.987526. The separately sampled vehicle-minus-host offset interval is approximately -0.572 to +0.452 seconds. That supports the guidance-stop association but does not timestamp the user's physical click exactly.

**Correction to a possible interpretation:** absence of a new TCP DisplaySink selection event does not mean the factory had no DisplaySink subscription. It was renewing and receiving acknowledgments through the first checkbox experiment. The checkbox did not force a fresh decoded destination selection. The height overlay occurred in a window without B009 subscription renewals, while V1 drawing traffic was present. This weakens the idea that the height rectangle itself demonstrates the active PiP path; it does not prove where the rectangle is rendered.

B003/8002 payloads in these captures begin with NMEA text such as `$GLGSV`; they must not be mistaken for image frames merely because they are large or frequent. Contents remain private because the stream may contain positioning data. The restored capture also contains V1 bitmap traffic after its return; the earlier `events: []` result concerns only the narrow native-PiP binding decoder, not all B006 activity.

The next implementation requirement remains receiver-selected destination plus a demonstrable pixel association. Reusing a factory subscription endpoint or inventing a HUD selection is not justified by these observations. No additional car session is requested by this offline review.
