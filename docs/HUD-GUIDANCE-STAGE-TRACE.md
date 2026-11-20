# Guidance stages and the fourth switch distance

19 November 2026, offline follow-up to the corrected PiP and high-bitmap tests.

## Observed outcome

The corrected native 277×160 custom marker appeared in the instrument cluster only; the windshield showed the test arrow. Both inline high-bitmap cases (third switch 92 versus 1000, distance 461) showed the stock roundabout rather than the custom image. These results do not establish that the fourth switch, 70, is the missing windshield gate. V1 was subsequently restored and its fifteen file/configuration comparisons passed; that restoration is separate from this analysis.

## Exact native evidence

The current-state body has four doubles at offsets 22, 30, 38 and 46. The saved values are 10000, 3000, 92 and 70. Native constructor/sender evidence identifies these as the sequential `GuidingStateSwitch` vector, rather than coordinates or image dimensions. The fourth field is index 3; naming it GS4 does not prove its rendering semantics.

In the captured controller parser `0xd47b48`, the vector length is bounded to four. The first output is a fixed value; indices 1 through 3 are copied from their corresponding incoming doubles and divided by ten (`0xd47ca0`–`0xd47cb0`). Nothing in this parser routes Screen output or changes a DisplaySink selection.

The controller method identified by its `isMainPhaseForPIP` diagnostic string begins at `0xa78170`. It finds the current maneuver/DR point and, for the normal valid-index path, reads the phase then checks **phase > 2** (`0xa782c4`–`0xa782d0`). Both phase 3 and phase 4 satisfy the predicate. `tools/verify_pip_main_phase.py` executes those actual ARM instructions with eight phase values and no intercepted imports. This is a producer-side predicate, not an emulation of the instrument cluster.

Direct callers at `0xa787b4`, `0xa79a7c`, `0xa7a31c` and `0xa7ae44` use the Boolean to decide whether to update their PiP maneuver path. None of these call sites changes the predicate to equality with 4. Other guards remain, including current-maneuver state and action-specific handling; this trace does not declare every phase-3 maneuver visible.

NavigationFully's `CGVManeuverStateItem` serializes the switch list into an output data chunk around `0x87ac98`–`0x87ad14`. That is another producer representation of the list, not the physical receiver's comparison against distance.

## Consequence for the next decision

There is no recovered native proof that windshield PiP requires only phase 4 or that crossing the fourth switch changes B009 selection 1 to 0. The captured controller explicitly permits phase 3 for its main PiP path. The corrected custom producer already supplies guidance type 8402 metadata directly; it does not wait for that factory producer predicate.

A receiver may still use the fourth distance for its own layout selection, but that remains a separate unproven claim. The failed 92/1000 comparison does not justify an automatic new car trip changing 70. Resolving that question requires the receiver's actual stage/route consumer or a retained capture showing the causal selection transition. Keep the local Screen route, B009 cluster negotiation, guidance-stage values and windshield rendering as distinct contracts.

## Native-verified distance mutation

`tools/b006_distance.py` implements type29/tag4 distance bodies. The retained 57-byte body contains model identity, bar-graph byte, numeric distance double, byte-counted segmentation data, byte-counted UTF-16 wire text, unit enum and u64 expected arrival. The numeric double occupies body bytes23–30. `replace_distance` changes only those eight bytes and preserves every other field; finite values0–10000 are accepted for offline preparation. It neither transmits nor changes stage thresholds.

`tools/verify_distance_native.py` executes captured serializer `0xbb6970` for distances461,92,70,69 and0. All40-byte payloads match exactly, including actual native double byte order, vector-length backpatching, empty-string UTF conversion, unit enum and arrival timestamp. Only stream snapshot/write boundaries are supplied. Three codec tests cover retained-byte roundtrip, isolated field changes and rejection of malformed/nonfinite values.

The accepted profile remains SHA-256 `f621e800338a3225f9fecf20f98b6938034aafb4f6bebb208e1ea156b89f4791`; the current19November keepalive recovery reference contains the same `supra-profile.bin`. Private archive path: `outputs/style-car-session-2026-11-19/keepalive-install/candidate-reference/supra-profile.bin`. A stage-transition experiment can now preserve all other graph fields exactly, but this is not yet proof that any distance transition selects the windshield. The unit enum is preserved as3 without inventing a display-unit meaning.
