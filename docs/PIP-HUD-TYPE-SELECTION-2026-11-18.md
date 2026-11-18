# HUD guidance-type selection: exact predicates

Offline investigation; V1 unchanged. No car contact, runtime patch, or new live test. **No larger-windshield repair is established.**

## New resolved routing condition

The retained controller's helper `0xa2756c` reads the cached HUD flag at manager +0x18. If set, it returns type class 2; otherwise it returns the configured Kombi type at +0x14. The nearby setter's diagnostic explicitly identifies +0x14 as Kombi type.

`0xa8699c` then supplies two **individual candidate IDs**, not an inclusive range:

| Class | Candidate A | Candidate B |
| --- | ---: | ---: |
| Kombi type 0, HUD flag clear | 4301 | 4402 |
| Kombi type 1, HUD flag clear | 5301 | 5402 |
| HUD flag set (class 2) | 8301 | 8402 |

The earlier description of these as ranges was incorrect. Helper `0xa864a4` compares a candidate for exact equality against the maneuver's available-type vector. `0xa86660` chooses the primary type and appends supported candidates:

- Preference byte at utility +8 nonzero: A is primary when present; otherwise B can be primary.
- Preference byte zero: B is primary when present. A can be appended, but A alone leaves primary zero and returns failure.
- Neighboring integers do not match. Arbitrary geometry or resource IDs are not guidance-type IDs.
- Constructor `0xa86524` initializes the preference byte to zero. This is a constructor default, **not proof that the byte remained zero in the failed live run**.

The already traced sink-switch task calls this resolver and writes the selected type to job +0xc only on success. A failed selection logs an invalid new guidance type and does not make that assignment. This is a factory producer routing predicate; it does not show a receiver accepting our pixels or allocate a windshield canvas.

## Execution verification

`tools/verify_pip_guidance_selector.py` executes the actual selector and membership instructions against the exact controller SHA-256:

`71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`

Forty cases cover HUD flag set/clear, Kombi type 0/1, both preference values, empty availability, A only, B only, both, and a neighboring unsupported integer. All selected IDs and success results match the predicates above. Vector clear, append and indexed-access routines are substituted at their ABI boundaries; the selector, cached-state helper and membership comparisons are executed. No receiver or physical transport is simulated.

```sh
python tools/verify_pip_guidance_selector.py /private/NavNBTEvoController
```

Private evidence includes bounded disassembly and each case's available, selected and appended IDs. Test vectors are controlled inputs, not recovered live availability lists.

## Why this is not yet an actual fix

The retained navigation-phase system log did not yield PiP/GuidanceType/RICManeuver/SinkSwitch diagnostics establishing the live available-type vector. The B009 recording proves destination selection and completion, not these internal job fields. Neither establishes the cluster's association between our new producer endpoint, native pixels, PiP resource and windshield output.

Changing the preference byte, advertising unsupported guidance types, or forcing the HUD flag would be a speculative modification of the factory producer and would not prove the custom path. None was implemented. The DisplaySink codec remains offline-only; the old live marker entry remains retired.

The precise evidence boundary is unchanged: we have factory HU producer routing code and receiver control messages, but no established receiver pixel-binding implementation or successful custom native-PiP trace on this Supra. Do not label additional HU selector tests as a receiver fix. A larger-display fix cannot presently be verified from these artifacts alone.

See [DisplaySink replay](PIP-DISPLAYSINK-IMPLEMENTATION-2026-11-18.md), [producer/receiver distinction](PIP-SINK-CONTRACT-GAP-2026-11-18.md), and [failed marker result](PIP-REVISION2-RESULT-2026-11-18.md). No new discovery trip is requested.
