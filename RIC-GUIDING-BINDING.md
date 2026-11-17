> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# Guidance image-reference and session trace

Offline analysis, 16 November 2026. Controller SHA256:
`71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`.

## Image upload is followed by a different model message

The factory `sendRoundaboutHighElement` at `0xab4600` references an image through **B006 method 11 (setGuidingData), variant 7**. This is distinct from method 3 resource upload and method 10 setManeuverData. The latter carries maneuver descriptions and is not the direct picture-reference serializer traced here.

Evidence chain:

- `0xab46b8` calls variant constructor `0xaaff40`, which stores literal tag 7.
- `0xab46d0` calls `0xab4114`, logged MyRicSetGuidingDataCall.
- Generated request `0xbc109c` sets method 11 at `0xbc11a4` and calls body serializer `0xbc1024`.
- Body: u32 handle, u32 model ID, u8 model type (0..50), u32 payload length, u32 variant tag, payload. All integers are big endian; variant length excludes its own field and tag.
- Union `0xbc0ef4` dispatches through `0xbc0ebc`; tag 7 entry `0xbc0d6c` selects `0xbb03dc`.
- Tuple chain `0xbb0344` -> `0xbb02a0` -> `0xbb0208` -> `0xbae728` -> `0xbae690` -> `0xba4b48`/`0xba4ab0` establishes the inner fields below.

Tag-7 payload is **11 bytes**:

| Field | Wire form | Constraint / primitive |
|---|---|---|
| Inner model ID | u32 | 0xba2ff0 |
| Inner model type | u8 | 0..50, 0xba4a28 |
| Maneuver type | u8 | 0..5, 0xbac0d8 |
| Drive direction | u8 | exactly 1 or 2, 0xbafa3c |
| High-guiding picture resource ID | u32 | 0xbb0394 -> 0xba2ff0 |

Total body: **28 bytes**. No XY coordinates, priority, lifetime or windshield selector occurs in this particular payload. The names follow the sender's log; numeric enum meanings beyond the validated ranges are not inferred.

At `0xab4680`, the sender first checks resource availability through `0xaad7f0`. If unavailable, it writes `0xffffffff` as picture ID. Otherwise it selects the already mapped resource ID at record+0x20 for selector 1 or +0x24 for selector 0. Caller `0xa8ba28..0xa8ba3c` populates those mapped fields before dispatch. A raw GV image ID cannot simply be copied into the remote reference.

This closes a concrete picture-reference message format. It does **not** establish the enclosing active maneuver/list/control graph, independent client acceptance, or visibility of this element on its own. The factory element being named “roundabout” is not evidence that any arbitrary image is accepted in every context.

## Session selector has two factory identities

`0xab3670` dispatches selector 0 to `0xab3408` (sendCreateICRequest) and selector 1 to `0xab353c` (sendCreateHMIRequest):

| Selector | Identity | Component | Vendor |
|---|---|---|---|
| 0 | BMW.IC.Guidance | ICGuidanceControl | BMW |
| 1 | BMW.HMI.Roadbook | RICController | Harman |

These are two existing factory roles, not proof that a third client can allocate an independent windshield surface. Do not confuse this role selector with DisplaySink's 0=HUD/1=Kombi navigation selection. Both use small integers but are distinct state machines.

Connection handler `0xab3788` clears handle +0x1c and flag +0x8c when disconnected (`0xab37b4..0xab37c0`). On connection it dispatches create then sets the flag. Therefore that flag alone is not proof that create has completed. Create-result `0xab3108` stores the returned handle and delivers configuration to `0xa2625c` before notifying its local observer. Error handler `0xab3688` retries create on code 4 while the flag is set. The meaning of code 4 is not assigned here.

## Resource removal is role-specific

`MyDisposeResourceNotification` handler `0xa8c150` logs separate DisposeResourceId4HMI and DisposeResourceId4IC. At `0xa8c1a8..0xa8c208`, selector 1 uses the first ID; the other branch uses the second. Each skips `0xffffffff`, then calls `0xab2174` -> `0xab2104`, supplying the current instance handle and selected resource ID to method 8.

This establishes which resource identifier gets released. It does not establish an automatic timeout, model-reference removal, or completion of remote visual erasure. Disconnect clears local state; no remote erasure can be inferred from that store. Instance disposal remains a separate method 7 operation.

## Code and validation

`tools/ric_guiding.py` encodes the explicit tag-7 body and decodes method-11 packets with bounds, enum, length and inner/outer identity checks. Unknown variants remain opaque hashes. It has no network transport and no default factory identifiers.

Nine new tests include a fixed byte vector, every truncation, invalid field values, length mismatch, unknown variants, identity mismatch and packet rejection. Full suite: **128 tests pass** using the analysis environment. An initial run with system Python lacked the existing ELF-analysis dependency; rerunning in the project's analysis environment resolved those two import errors.

Audit of **all 144 saved stream-*.bin files** found four method-11 requests and four empty successful responses, zero parse errors, and **no tag-7 request**. Counts are not request/response correlation. This validates the generic envelope on retained traffic; the 11-byte image-reference payload remains static-derived and synthetic-tested, not vehicle-accepted.

## Actual drawing-test status

Not yet executable as an independent windshield test. We now have bitmap upload plus a concrete factory picture-reference message, but not a complete independently owned visible graph or a remote cleanup guarantee. No marker was drawn, no car operation occurred, and no further capture trip is requested. These results narrow the implementation work; they do not justify replaying factory handles, identities or graphs as our own app.
