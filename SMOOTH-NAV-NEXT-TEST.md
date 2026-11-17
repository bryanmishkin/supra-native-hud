> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# Smooth RPM: explicit empty model and navigation yield

Prepared offline on16 November2026, after the verified smooth30-second run.

## Circle: a distinct next candidate

The previous no-detail and road-only trials never replaced the selected high-guiding model with an empty union. They omitted its initial setup, while their common cleanup still sent a tag7 RoundaboutHighElement with picture ID0xffffffff. An absent picture ID and an empty model variant are different wire values. Retained server model state is therefore a plausible contributor to the persistent circle, not an established cause.

The captured controller's serializer provides concrete evidence: at0xbc0fa4 it compares the variant tag with zero, at0xbc0fa8 branches to0xbc0ff0, skips member serialization and backpatches a zero payload length. The new `encode_empty_guiding_body` emits that17-byte envelope: handle, model ID, model type, length0, tag0. Static source SHA256:71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a.

`--graph-variant empty-detail` explicitly writes the empty variant to our selected high-model slot, references that slot from the description, retains captured direction8 and preserves the coming-road bitmap binding. It does not delete the shared instance or change unrelated factory IDs. A live-RPM run with this variant requires double buffering and does not repopulate the empty model while alternating bitmaps. The proven full cleanup sequence is retained; it still clears the high-picture reference using the previously live-verified tag7 form.

This candidate is not a confirmed circle fix. An empty variant may be rejected, ignored, hide the tachometer or leave the circle. One short visual test can discriminate it. The existing control remains available and unchanged on the wire.

## Navigation: explicit cooperative withdrawal

The smooth live loop now checks a local `navigation-yield.request` at freshness/binding checkpoints. `tools/request_navigation_yield.py TRIAL_DIRECTORY` creates that request only for an active live-RPM trial. It neither starts factory guidance nor changes anything in the car itself. A valid request stops further updates, attempts full graph withdrawal and removes all tracked bitmaps, including both slots if interruption occurs mid-switch.

The runner writes `navigation-handoff.json`. `protocol_ready:true` requires the yield reason, a successful trial cleanup status, every cleanup acknowledgement, bitmap disposal and absence checks, preserved factory instance and canceled forward. It always requires visual confirmation and never automatically resumes. Missing acknowledgements, transport failure, bad data or a merely expired duration do not produce a navigation-handoff success. A successful protocol report alone is not permission to start guidance before visually checking removal.

This is an executable handoff for an operator or future navigation integration, not automatic detection of factory navigation. The separate evidence reducer still cannot establish radio-idle or exclusive ownership. Starting factory guidance before withdrawal is confirmed remains outside this test. No shared navigation state is replayed to resume a route. Transport loss still prevents guaranteed remote erasure; readiness remains false.

## One next session

1. Park outdoors, remain stationary, guidance stopped and selector closed. No engine revving needed. Establish existing verified access and confirm normal displays.
2. Run `empty-detail` with the saved3500 static bitmap for three seconds. Record tachometer visibility, circle/replacement-icon visibility and both displays returning normal. Verify all cleanup results before proceeding.
3. If the candidate is visually successful, use `empty-detail` for the live test; otherwise use the known smooth `control`. Run double-buffered measured RPM for up to30seconds. Observe smoothness and numbers, without needing to change engine speed.
4. While that live window is active, send the local yield request. Do NOT start factory navigation yet. Wait for `protocol_ready:true`, then confirm all test graphics disappeared from both displays. If either condition fails, stop the procedure and inspect cleanup; do not restart automatically.
5. Start factory navigation and verify both displays. Stop guidance, check radio selector/iDrive and normal HUD. Save operator answers and raw evidence before unplugging.

The private kit supplies `run-stage.sh circle|live-control|live-empty|yield`. A new result directory is mandatory. `live-empty` is used only after the short candidate passes. Yield is a separate invocation pointing to the currently running trial. It may take longer than one checkpoint to complete cleanup; wait for the result, not a fixed delay.

## Offline verification

215 Python tests pass, including a fixed empty-variant vector, exact-token request validation, active-live-window enforcement and refusal to report handoff on incomplete cleanup. Six injected-transport simulations cover unchanged control, empty-detail, yield while sampling, yield mid-reference-switch, invalid RPM and lost upload acknowledgement. Both yield cases removed tracked resources without disposing a referenced bitmap and reported readiness; invalid RPM withdrew but did not claim a navigation handoff; lost acknowledgement reported uncertainty and no readiness. All879 control requests match the prior smooth-control simulation byte-for-byte. Simulation counts differ from actual car timing.

Python-only changes; the native renderer and its previously built ARM artifacts are unchanged. No vehicle contact occurred during this work. The next test is ready; neither circle removal nor automatic simultaneous navigation coexistence is claimed solved.
