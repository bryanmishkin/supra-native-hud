# Direct PiP producer: missing sink contract

**No actual larger-windshield fix is established.** This offline review identifies a concrete omission in our failed runner and corrects the interpretation of the earlier session/job trace. V1 runtime, install files and baseline tags are unchanged. No car connection was attempted.

## Correction: factory producer jobs are not the receiver

The traced `NavNBTEvoController` session/job chain belongs to the head unit's factory producer. It passes a RIC maneuver identity to NavigationFully content and attachment. Our experimental helper bypasses NavigationFully and posts its own Screen window. The working G30 reference likewise supplies its own native producer.

Consequently, missing HU factory jobs are not an established explanation for our failed custom stream. The earlier bounded job-consumer execution remains valid, but it tests conditional HU behavior—not a cluster receiver. Do not spend another car visit creating or borrowing those factory jobs without evidence that the custom path needs them.

## Concrete missing step compared with the reference

Pinned ryseek source remains `a0242e1c30d17b138845c18d6bf86ae0cd99ead6`:

`milestone-7/src/cluster/video/native/control.hpp`:

1. `connect_sink()` opens DisplaySink TCP to port 30503, bound to its producer address.
2. It advertises the connected socket's actual local port in a SOME/IP service-discovery subscription for B009 event group 1.
3. `sink(true)` accepts a specific receiver-selected geometry/destination and sends the matching completion.
4. `start()` only then starts Guidance, and only for its supported cluster destination. HUD selection pauses that reference's video.
5. Subscription renewal, later switch events and unsubscribe are part of its lifetime.

Our failed `pip_trial.py` opens only Guidance (through the forwarded connection). Its native helper explicitly sends no DisplaySink requests. It neither subscribes nor obtains a receiver-selected destination for its stream. Matching `PIP_BINDING` JSON and seeing a local Screen window cannot substitute for this missing control-plane contract.

This is a proven implementation difference, **not proof that adding B009 alone fixes Supra windshield delivery**. The reference uses a distinct producer IP, and the receiver's mapping from client endpoint to native pixels remains unknown on the Supra. Do not copy that address, seize the factory subscription, fabricate selection 0, or assume a completion creates an independent surface.

## Replayed retained evidence

`tools/audit_pip_sink.py` reassembles existing captures, strictly decodes B009 messages and preserves direction/timestamp. It does not connect or transmit.

| Capture | Packets | B009 evidence | Parse errors |
| --- | ---: | --- | ---: |
| Earlier factory navigation capture | 13,661 | Two selection events and two completions | 0 |
| First custom marker | 4,781 | None | 0 |
| Revised custom marker | 4,686 | None | 0 |

The factory events are scale 1, 460×237, selection 1, on cluster port 30503 to HU port 65497; reverse-direction completions contain `0100`. Existing controller tracing identifies selection 1 as Kombi, not HUD. These are factory-client observations and cannot be assigned to our marker producer.

No events within the marker windows does not prove the factory had no retained sink state. It proves neither a missing physical cable nor unsupported hardware. Combined with source inspection, it establishes that our runner does not reproduce the reference's complete startup contract.

Capture SHA-256:

- Factory: `0976202b21605829b4bef74d62dd1b724b7dc1fce85c23e4a63e8ccd696aced3`
- First marker: `58b0f0497cc03558719dc82d2031a2c5a8b0fbfbf26b545add0e348df531e893`
- Revised marker: `a58ce81531c3d7e0d8ceb5777d48a20e7798df29278026a0cc1cb21d0c655f09`

## Code corrections

- Retire `pip_trial.py --execute` before any file read, connection, or drawing. Offline plan generation and the bounded protocol regression harness remain available. There is no bypass flag for retrying the failed candidate.
- Rename the runtime result to `producer_contract_verified`; explicitly record `receiver_binding_verified = false`. Historical JSON is preserved unchanged, with its old field interpreted as local contract matching only.
- Add strict offline B009 audit and malformed/truncated/unsupported event tests. This decoder does not return a readiness grant.
- 17 focused PiP tests pass, including cleanup regressions and a check that the retired CLI rejects execution before reading nonexistent input files.

## Remaining proof needed

Resolve the receiver's producer-endpoint/native-stream association and windshield destination contract. Neither the captured HU job chain nor the G30 cluster implementation supplies that missing receiver behavior. Until that edge is established, a subscriber-only implementation would be another hypothesis, not an actual fix or a justified car test.

The investigation has corrected a concrete false readiness assumption and isolated an omitted startup stage. It has **not** demonstrated custom pixels in a larger Supra windshield area. V1 remains the working fallback and is untouched.

Credit: ryseek, Sq00ky/nanaisu and the NBT-AAD contributors. See [reference provenance](PIP-G30-REFERENCE-2026-11-18.md), [identity consumer](PIP-CONSUMER-AND-ID6-REVIEW-2026-11-18.md), and [failed live result](PIP-REVISION2-RESULT-2026-11-18.md).
