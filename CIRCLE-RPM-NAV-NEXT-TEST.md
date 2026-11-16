Live outcome: RPM passed 40/40 reads; neither circle candidate removed the circle. Cleanup and factory-function checks passed. See [CIRCLE-RPM-LIVE-RESULT.md](CIRCLE-RPM-LIVE-RESULT.md). The procedure below is retained as the executed test record.

# Circle isolation, live RPM input and navigation — 16 November 2026

## Video evidence

The supplied IMG_1889.mov is 18.188 seconds. Inspected frames around 3, 7 and 11 seconds show 1000, 3500 and 6500 in the windshield, respectively. The high-value frame also shows five bright indicators. The circle is below the custom image. This corroborates the earlier operator report and supports treating the navigation symbol separately from the custom raster; it does not by itself identify the exact responsible field. The camera moves by the end, so the video alone does not prove complete cleanup. The previous visual and protocol checks remain that evidence. Original video and selected extracted frames are private Drive evidence, not GitHub source.

## Circle candidates

The proven control builds a high-roundabout detail model (method11/tag7), references it from the description, and sets description direction14. The bitmap that actually became visible is also referenced by the coming-road icon list. Two explicit variants now exist in `run_shared_roadicon_trial.py`:

| Variant | Setup difference from control | Purpose |
|---|---|---|
| control | None | Known-good tachometer and circle |
| no-detail | Omit detailed-roundabout setup; description detailed reference absent | Isolate whether detailed model causes the circle |
| road-only | Same omission; direction14 becomes captured direction8 | Isolate the direction-dependent built-in symbol |

Direction8 is an observed factory enum, not a confirmed “no icon” enum. The second candidate may show a different built-in arrow, suppress the tachometer, or have no effect. Neither candidate is labeled fixed. Both preserve road-icon binding, support models and the known cleanup sequence, including its final high-model reference clear. Tests verify the intended wire fields and cleanup; only a visual test can establish circle removal.

## RPM source and native connection

The earlier actual Supra replies are `41 0C 0F 6E` (987.5 RPM) and `41 0C 0A 44` (657 RPM), requested from DME address12 through ENET gateway169.254.106.96:6801. The locally preserved reference project's SIGNALS.md and diagnostic implementation agree on two big-endian bytes divided by four. These are captured values, not simulated discoveries.

`tools/rpm_feed.py` implements that exact read-only request, with bounded frame sizes, response deadlines, ECU/source matching, negative-response rejection and fragmented TCP reads. Explicit `--execute` is required; otherwise it prints a plan. It sends no session-control, security, coding or write service. Sampling has a ten-second scheduling window, at most40 requests and at most4Hz, plus at most the last response deadline. Each request uses a fresh connection to avoid confusing an old delayed reply with a new sample. The raw replies and monotonic timing are saved as JSONL. Latency is measured, not assumed.

`src/rpm_input.cpp` connects a positive RPM reply to the existing native Input.rpm consumed by HudCore and the bitmap renderer. Native tests cover captured fractional values, negative/malformed responses, order, 300ms freshness, unknown navigation/ownership suppression and active-navigation yield. Request-start time is the conservative sample timestamp. Invalid data invalidates the sample; it never reuses the last number.

The sampler and native decoder are built/tested components, not yet an end-to-end live HUD loop. It would be misleading to show a sampled number for the existing three-second static window as live RPM. Continuous resource updates, bounded withdrawal on stale data and an exclusive/cooperative navigation contract must be established before connecting live readings to the display sender.

## Factory navigation

`factory_activity.py` reduces observed factory guidance state messages and excludes this test client's own packets. It reports unknown when stale; active/transition can be recorded as a conflict. Guidance-idle alone never grants drawing permission, because radio activity and shared-session ownership are still unknown. This is an offline evidence reducer, not a connected live detector or an automatic cleanup controller.

Do not dispose the factory instance, replay a factory route, or automatically cancel factory navigation to reclaim drawing state. Existing production suppression remains unchanged. The next test continues the proven staged handoff: custom test finishes and disappears, then factory guidance/radio is checked. No simultaneous navigation takeover experiment is included.

## Next session, one bounded plan

1. While parked outdoors, engine running only for HUD visibility, keep guidance and selector stopped. Read RPM for about ten seconds and compare it with the factory tachometer at idle; no revving required. Save raw replies, latency and freshness statistics. This phase needs no SSH or HUD writes.
2. Run no-detail for three seconds with the same 3500 synthetic bitmap. Record separately: tachometer visible, circle absent/present, any replacement icon, and both displays normal after cleanup. If the tachometer remains and circle is gone, do not run the second variant unnecessarily.
3. If needed and cleanup is verified, run road-only for three seconds and collect the same answers. Every invocation stops after cleanup; no unattended retry or automatic succession.
4. If appearance is ambiguous, the unchanged control is available for one comparison. Stop on any cleanup uncertainty or abnormal factory display.
5. After all custom graphics are gone, start factory navigation, verify both displays, stop guidance and check radio/iDrive. Save operator results before unplugging.

Use the private prepared `run-stage.sh` launcher with phase `rpm`, `no-detail`, `road-only` or `control`. It requires a fresh output path; RPM additionally requires the current Mac ENET address. No car contact was made during offline preparation.

This test resolves two specific questions: which known graph fields can remove the circle without losing the tachometer, and whether the established RPM read path supplies sufficiently fresh repeated samples. Automatic navigation coexistence and continuous live HUD updates are not claimed ready.

## Validation completed offline

210 Python tests passed. Native C++98 tests passed on 32-/64-bit Linux and the RPM adapter test passed on Mac. The complete QNX ARM build succeeded, including rpm_input.o. Three mocked circle-variant runs verified fields, preserved road-icon binding and successful cleanup/absence; the control's 32 requests match the prior 3500 replay byte for byte. These are client and build checks, not a claim that the circle is removed in the car.
