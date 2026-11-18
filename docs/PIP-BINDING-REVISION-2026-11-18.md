# PiP image-binding revision — 18 November 2026

**Superseding live result:** [revision-2 test failed to display custom pixels](PIP-REVISION2-RESULT-2026-11-18.md). Only the right-turn arrow appeared. Cleanup and unchanged V1 return passed. Retain the procedure as historical; do not repeat this candidate as a ready image-binding fix.

The last car attempt displayed a right-turn arrow, not the custom marker. Offline review found a format-selection assumption and produced a corrected, bounded candidate. **The cause of missing pixels is not conclusively established, and larger windshield output remains unproven.** V1 is unchanged; no vehicle connection occurred during this work.

## What explains the arrow

The saved request graph explicitly sets maneuver direction 7 in description `0x0f000004`. The owner saw that right-turn symbol. The native producer's 255 successful posts and the resource ACKs establish local output and accepted requests, respectively; neither establishes receiver consumption of our image. There were no B009 messages in either recording, which does not reveal the previously selected sink.

## Format selection corrected

The old controller selected depth 1 simply because the create reply advertised supported depth 1. The factory client's checks show those advertised fields are upper limits:

- `0xaadd94`: reads supported depth at configuration `+0x9c`, compares it with the proposed depth, and logs only when proposed depth exceeds the limit.
- `0xaadd48`: does the same for packaging at `+0x9d`.
- `tools/verify_pip_format_limits.py` executes these actual captured ARM routines with Unicorn. All **15 cases** agree with the upper-limit comparison. The logging dependency is intercepted; no receiver or hardware code is executed.

The revised descriptor selects **depth 0**, matching ryseek's working native producer/reference selection, which is within the Supra's advertised limit of 1. This repairs the assumption that a capability maximum determines the correct source format. It does **not** establish that depth 1 caused the failure or that enum 0 has a particular named pixel format on this receiver.

Packaging remains 0, the Supra's advertised maximum. We do not copy the G30's packaging 1 or 800×480 descriptor, which exceed this saved Supra profile. The candidate retains a 320×200 descriptor and 800×480 native backing. Whether this receiver accepts that crop/backing relationship is still unproven. The G30 reference registers its backing dimensions; that difference must not be hidden by calling the new candidate a proven transport fix.

An exact comparison against the failed car plan finds **one changed wire byte**: method-3 body offset 26, depth `1 → 0`. Every graph and withdrawal body is identical. The description ID, metadata ID, resource ID, dimensions, direction, distance, threshold, packing, selected output and cleanup are held constant. This is a focused format comparison, not a parameter sweep.

## Producer and descriptor binding checks

The helper emits a versioned `PIP_BINDING` record before its first-post confirmation. The controller requires exact agreement on description ID, resource ID, backing/content dimensions, selected depth/packing, Screen format and metadata ID bytes before activating any graph. An older helper or mismatched binding triggers disposal/absence checks for the attempted resource without graph activation. Packaging rejects an old helper without this handshake.

The native metadata ID remains `0f000004`, matching the selected description identity. Factory tracing establishes a RIC-maneuver content key and metadata field, but does not yet prove the receiver's mapping from this particular emitted strip to resource `0x02000004`. The handshake prevents two parts of our app disagreeing; it is not receiver-side validation.

The producer also records `/dev/screen/0/dpy-2` after its first successful post and immediately before removal. This supplies active output state within the same attempt, instead of relying only on before/after snapshots. Snapshot errors/truncation are recorded. They do not substitute for visual confirmation.

## Built and tested

- 14 focused PiP tests pass, including stale/mismatched producer refusal, no overwrite of an occupied resource, rejected/lost request cleanup handling and no visual-success claim from ACKs.
- 15 actual factory ARM limit cases pass.
- Separate QNX ARM producer and passive recorder compile with warnings as errors, networking disabled, and pass captured-runtime dependency/import audits.
- Final producer SHA-256: `681df1d01b8270ae2a1a5e1e94d5c844063e15901d8fbeaf6ac54e97b22b7e91`.
- Exact V1 reference manifest: `ac903624ebda36039885a2d2fb36cc3f5d9403f22b554d448ab8ae584268c6c7`; V1 source, installed files and tags are untouched.

## Next bounded test and acceptance

Use only the revision-2 kit and current controller together, following [the parked test procedure](PIP-MARKER-TEST.md). One 30-second-total producer run; announce watch after graph activation. Setup consumes part of the window. Capture passive traffic and the producer's active output snapshots in that same attempt. No driving, RPM changes, factory window borrowing, display-mode changes or fabricated sink notification.

Success requires the actual white rectangular border/cross with cyan/orange corners in the windshield—not a turn arrow—followed by confirmed image withdrawal, resource absence and verified original V1 return. A cluster-only marker does not pass the windshield goal. A second arrow-only result rejects the depth-selection hypothesis; do not cycle through IDs, packaging or display outputs live. Reuse the collected evidence offline.

This package is an executable controlled candidate, **not a verified fix or an assurance that another car session will produce pixels**. Its remaining native transport/receiver uncertainty is explicit above.

## Reproduce and provenance

```sh
python3 tools/verify_pip_format_limits.py /private/NavNBTEvoController
python3 -m unittest discover -s tests -p 'test_pip*.py' -v
```

Controller SHA-256: `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`. Prior primary PCAP SHA-256: `58b0f0497cc03558719dc82d2031a2c5a8b0fbfbf26b545add0e348df531e893`.

Credit: **ryseek**, **Sq00ky / nanaisu and the Supra Android Auto contributors**. Reference source remains pinned to `a0242e1c30d17b138845c18d6bf86ae0cd99ead6`; its G30 native profile supplies depth 0. Scoped third-party headers and required PolyForm Noncommercial notices remain unchanged. See [the reference review](PIP-G30-REFERENCE-2026-11-18.md) and [notices](../THIRD_PARTY_NOTICES.md).
