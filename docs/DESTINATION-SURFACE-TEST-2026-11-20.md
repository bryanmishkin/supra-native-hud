# Destination-picture surface probe

A new bounded test is implemented, separate from the RoadInfo layout and the failed PiP selection experiments. It uses the factory destination-reached picture model, B006 method11/type49/tag10. It is **not yet proof of a larger windshield surface**. No vehicle was contacted and installed V1 remains untouched.

## Why this is grounded in the car's data

The TCP scan of52 unique retained captures found three type49/tag10 messages, each with an absent picture reference. Their descriptions link that exact model as the detailed maneuver, with direction10. The selected factory witness supplies the current-state and zero-distance messages as well. One recording has a TCP gap; the count is not a claim of complete vehicle traffic coverage.

Actual controller code establishes the missing field's meaning:

- Constructor `0xa40384`: model type49, maneuver0, stopover number and source picture.
- Sender `0xab4a58`: high destination-reached picture conversion.
- Wrapper `0xaaff94`: variant10.
- Native writer `0xbaefb0`:12-byte payload `model ID, model type, maneuver, stopover u16, picture ID`.
- Builder `0xa4751c` links the returned model into the maneuver description at `0xa477d8/0xa477e4`.

Executing the captured ARM writer matches the observed payload and both reserved bitmap IDs, plus the absent reference. This establishes the wire contract and graph attachment, not receiver layout behavior.

The receiver advertises five model49 slots at `0x31000000`. The test uses the last slot under the same stopped-guidance shared-session discipline as prior tests. This is not exclusive allocation of a new session. Neither a model count nor the picture contract implies a full-screen canvas.

## Exact experiment

The first30-second window uploads two150x36 images into the already reserved slots8/9:

- Cyan bordered1: the known RoadInfo reference.
- Border/cross marker: the destination model's picture reference.

The description binds the recorded destination model instead of the empty roundabout model. Its factory direction10, current-state payload and zero-distance payload are retained. Object identifiers are remapped to the selected test slots; previous/next route links are absent. The resulting single-item graph is a controlled combination of the captured destination state and the accepted test graph, not a claim that the factory previously displayed our pixels.

This tests **a different image-bearing renderer**. It does not change RoadInfo alignment, upload oversized resources, fake HUD selection0, replace a text cell, or repeat the roundabout/PiP tests.

Record whether the cross actually appears, its display destination, its complete boundaries, and its placement relative to the cyan reference and normal speed display. If the factory hides the reference, do not infer scale from memory: use the saved reference photograph and label the comparison as approximate. An arrow, finish symbol, cluster-only image, ACK or allocated bitmap is not success. A larger-area result requires distinct custom pixels outside the documented V1 footprint. If it renders within that footprint, record another bounded surface—not an enlarged canvas.

The second optional30-second window is the previously authorized `wide_tail_64` extent test. Its full green far edge must be visible outside the first reference. This can establish a complete second panel through RoadInfo; it cannot establish greater height or root-surface control. No old controls, alignment sweeps or Hz tests are in this batch.

## Lifecycle and tested failure behavior

`manage_road_list_session.py prepare --surface-batch` prepares exactly `destination_picture` then `wide_tail_64`. Its source hashes pin the runner and its dependencies. It requires the exact private factory witness and accepted V1 profile.

The manager verifies all15 current V1 files, cooperatively pauses V1, checks stopped state and requires visual clearance. Both reserved bitmap slots must be absent; an occupied slot stops the test. Each upload and graph action is journaled. WATCH NOW starts a full30-second static window.

Destination cleanup runs cancel, idle and empty list before clearing model49's picture. It completes the existing withdrawal sequence, then disposes only tracked images and verifies absence. **Any uncertain graph withdrawal retains the images for recovery instead of deleting potentially referenced resources.** Shared instance disposal is forbidden. The optional test does not start until protocol and visual clearance pass.

Offline validation exercises the actual trial/session code with30 lost replies,30 rejected replies, both occupied slots, cancellation, and journal failure. The existing road test suite still passes all140 lost-reply positions. These are transport/cleanup tests, not simulated receiver visibility.

After both windows, restore V1 through the established normal restart. Require owner-confirmed updating tach, all15 file hashes, advancing frames/samples/heartbeat, enabled and healthy supervisor, and no experimental output before unplugging. Do not clear fault markers to make restoration appear successful.

## Other newly traced models

Branch-high type3/tag5 and tunnel-high type13/tag8 now have strict codecs and captured-native serializer checks. Neither appeared in the retained52-recording TCP scan. They are **not scheduled** merely because their formats are understood. This avoids adding unsupported renderer guesses to the trip.

The main HUD compositor and editable parent boundary remain unresolved. This batch is ready to test a newly established picture attachment and the retained extent candidate; it is not a completed full-canvas unlock.
