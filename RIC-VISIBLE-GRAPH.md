> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# Active maneuver graph and cancellation

Offline analysis, 16 November 2026. Controller SHA256:
`71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`.

## Concrete chain recovered

The traced factory navigation chain is:

```
method 9 / tag 2 list state
  active_maneuver_id -> method 10 / tag 1 maneuver description
    detailed_maneuver_id -> method 11 guiding element
      tag 7 high-roundabout element -> picture_resource_id
        method 3 / tag 2 bitmap resource
```

These arrows describe references, not a complete proof of visibility. Other factory models (road, distance, maneuver state, lists and high-guiding image information) may be needed. The server's independent-client policy is not present in the captured head-unit client. The same model/resource ID must be resolved within its actual session, not copied from factory traffic.

The prior image-reference codec closes the last two arrows statically. This change recovers the first two arrows and validates their bytes against captured traffic.

## State and description wire formats

Both methods use the same outer shape: u32 handle, u32 model ID, u8 model type (0..50), u32 payload-byte length, u32 variant tag, payload. Numbers are big endian. Inner model identity repeats u32 ID and u8 type.

Method 9, tag 2 payload is **42 bytes**: inner model identity; u32 active and passive maneuver IDs; u8 guidance state (0..8); u64 expected-arrival value; u64 total-delay value; IEEE-754 binary64 route length; u32 icon-resource ID. Units for arrival/delay are not inferred. Full request body is 59 bytes.

Anchors: sender `0xab5238`, tag constructor `0xab01c8` stores 2; request method literal at `0xbbf868`; body `0xbbf6e8`; variant dispatch `0xbbf548` -> `0xbb07d8`. Tuple chain descends through `0xbb0748`, `0xbb06b8`, `0xbb0628`, `0xbb0598`, `0xbb0508`, `0xba6c74`, `0xba6bdc`, `0xba4b48`. State enum serializer `0xbb0480`; u64 `0xba37d8`; binary64 `0xba35d4`. Captures include a negative maximum-finite-double route-length sentinel; the codec preserves it, not zero or a guessed valid distance.

Method 10, tag 1 payload has a **45-byte minimum**:

| Field after inner identity | Wire form |
|---|---|
| Passive flag | u8 bool |
| Previous joined, previous maneuver | u8 bool, u32 |
| Next joined, next maneuver | u8 bool, u32 |
| Maneuver direction | u8 enum 0..58 |
| Current state, coming road, detailed maneuver, distance | four u32 IDs |
| Navigation events, lane guiding, points of interest | three arrays; each u32 **byte extent**, then u32 IDs |

Full body minimum is 62 bytes. Empty arrays still have their length field. Unavailable references can be `0xffffffff`; flags and missing references are reported without inventing consistency rules.

Anchors: sender `0xab5ff0` region, constructor `0xab0054` stores tag 1; request method literal `0xbb8bec`; body `0xbb8a6c`; variant dispatch `0xbb8904` -> `0xbb2f20`. Tuple chain: `0xbb2e90` -> `0xbb2e00` -> `0xbb2d70` -> `0xbab2e4` -> `0xbab254` -> `0xbab1c4` -> `0xbab134` -> `0xbab09c` -> `0xbaa764`, then common maneuver prefix through `0xbaa6d4` to `0xbaa48c`. Array serializer `0xbb1918` backpatches bytes at `0xbb1a20..0xbb1a34`. Boolean serializer `0xba9b54`; direction `0xbaad3c`.

## What the retained car traffic now establishes

Audit of all 144 saved `stream-*.bin` files found 34 method-9/10 requests, including **12 state messages and five descriptions**, with zero decode errors. All **17** recognized bodies re-encode byte for byte. Eighteen method-9 responses and sixteen method-10 responses were empty with success code; these are counts, not cross-direction transaction correlation.

The description's detail IDs match method-11 model IDs in the same navigation recording. Those actual guiding messages use variant **6** (three messages) and **10** (one), not the traced bitmap-reference variant **7**. Do not label untraced variants as bitmap, SVG or vector merely from their numbers.

The captured state sequence contains active state 2 with an actual maneuver ID, followed later by cancellation state 5 and idle state 0 with both active/passive references set to `0xffffffff`. This is concrete factory reference removal. It is not evidence that a newly uploaded bitmap resource has been disposed or erased, nor that a third client will be accepted.

Model type 33 in these state messages is a model enum. It is **not** configuration-variant 33 (bitmap configuration). Keep these namespaces distinct.

## Client transition rule and cleanup boundary

The client filter at `0xaaf350` compares previous/new state and branches through nine entries at `0xaaf36c`. Equal states are accepted. Allowed following states (including equality):

| Previous | Allowed following |
|---|---|
| 0 | 0, 1 |
| 1 | 1, 2, 4, 5, 8 |
| 2 | 2, 3, 4, 5, 6, 7, 8 |
| 3 | 1, 3 |
| 4 | 2, 3, 4, 5, 6, 7, 8 |
| 5 | 0, 1, 5 |
| 6 | 0, 6 |
| 7 | 2, 4, 5, 7, 8 |
| 8 | 2, 3, 4, 5, 6, 7, 8 |

Caller `0xa8f560..0xa8f5c0` inserts state 1 when leaving state 3 for cancellation 5, logged as `3->1->5`. This is a client sequencing rule, not the server's ownership or deletion policy. Sending cancellation is distinct from disposing a resource or instance.

## Built and tested

- `tools/ric_graph.py`: strict state/description decoding, explicit body encoders, preserved unknown variants, and the traced client transition filter.
- `tools/ric_graph_audit.py`: reads one ordered saved SOME/IP stream, follows references within client+handle, reports missing/untraced links, and prevents joins across separate invocations. Inner/outer identity mismatches fail. Initialize/dispose requests conservatively invalidate cached evidence; this does not assert remote erasure or actual initialization semantics.
- The audit never reports a partial chain as a visible surface. Synthetic complete chains are labeled reference chains only. Killing a process or clearing a cache is not a remote cleanup guarantee.
- **149 tests pass**, including fixed byte vectors, every truncation, malformed extents/enums, non-finite representation, negative sentinel preservation, all transition pairs, handle/client isolation, cancellation and lifecycle cache invalidation.

Run the passive analyzer on an already saved stream:

```
python3 tools/ric_graph_audit.py /private/saved-stream.bin
```

## Actual drawing-test status

Not ready for an independent windshield marker test. The recovered reference chain is substantially more concrete and its state/description formats are capture-validated. Remaining unknowns are which complete model set the cluster requires for the bitmap branch, what configuration it grants a distinct app identity, and what cleanup that identity gets. Those runtime/server behaviors cannot be established by encoding factory client messages correctly. No car connection, command transmission or new capture trip was performed or requested.
