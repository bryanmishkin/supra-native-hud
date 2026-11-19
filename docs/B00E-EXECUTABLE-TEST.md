# B00E IU trident experiment: executable and admission contract

19 November 2026. Offline preparation; V1 files and installation unchanged.

## What is now concrete

The captured HMI provides an exact path from a factory icon ID to CarouselElement's first serialized field:

- `CPeerICLabel::updateRICSVSCarouselLabel` at `0x2584b1c` calls container getter `0x258885c` (reads +0x48), retains the icon ID in SL at `0x2584c64`, and stores it at element +4 at `0x2584e68`.
- The two subsequent fields receive text resource IDs; the fourth is `0xffffffff` in this path. The element writer `0x292008c` emits these four fields in order.
- Factory `CPeerICList::updateRICCarousellist` explicitly checks model ID **0x6d** (`0x2585fcc`). The HMI mapping table pairs it with type **0x1c**. Config offset `0x1c000000` is not a justified replacement model ID.
- Historical retained recordings contain **27 actual Carousel model updates**, all four-item arrays, and matching focus selections. The new codec exactly re-encodes all 27 and the 12 recent Voice variants. The observed icons are type-7 preinstalled references, not uploaded bitmaps.
- `setRICBitmapResource` at `0x2592b44` explicitly compares width and height against configured limits (`0x2592b94`, `0x2592bc4`), constructs a type-1 bitmap with dimensions and RLE data, then posts the resource. This supports bounded smaller images; it does not establish display placement.
- Independently traced B00E method-3 serialization is handle, resource ID, type, variant length/tag, repeated resource ID/type, two BE-u16 dimensions, u32 byte count and bytes. See [removal contract](B00E-REMOVAL-TRACE.md) for independently traced check/dispose operations.

## What this experiment tests

Whether the **same icon-reference field** accepts a type-1 uploaded bitmap and renders it on the windshield. A factory icon in this field is proven; custom bitmap acceptance is not. The executable is a controlled receiver test, not proof that this feature already works or that it provides an independent canvas.

`tools/b00e_bitmap_trial.py` uses shared factory handle 100, Carousel model 0x6d and focus model 0x65. It never creates or disposes an instance, modifies startup, installs code, or changes V1. Shared use is not exclusive ownership. Only an explicitly admitted stationary test window with factory overlays closed is permitted.

## Required current-session admission

Before running, retain a **current-session full factory Carousel model body** and verify idle focus and clean V1 pause. Never substitute the historical research capture as a current snapshot. The runner refuses missing, stale or unrecognized admission data. If a current snapshot cannot be obtained, no B00E drawing occurs; this is not grounds for another blind trip.

Admission JSON fields:

- `verified_at_unix`: verification time, no more than 120 seconds before execution.
- `parked`, `v1_paused_cleanly`, `v1_hashes_match`, `factory_overlays_closed`, `focus_is_absent`, `same_session_snapshot`, `exclusive_operator_window`, `manual_recovery_verified`: each explicitly verified true.
- `configuration_body_hex`: exact current verified B00E create-response body. Must match retained profile SHA-256 `21ff4431fc9c2360bcac942688513004f8b1063a5cf19e30b334b5eb4e82d398`.
- `restore_carousel_body_hex`: complete method-11 body for this session's factory model 0x6d/type0x1c. Validated by the strict decoder.

These are evidence assertions, not generated defaults. The fixture builder does not create an admission file. Preserve the source captures and evidence that each assertion is true.

Run offline without arguments to inspect the plan. The live command requires `--execute --port LOOPBACK_FORWARD_PORT --admission CURRENT_JSON --bitmap-bgra FIXTURE --size 36 --output NEW_DIRECTORY`. Port is an already verified SSH forward; the tool only connects to 127.0.0.1, never chooses a vehicle address. Use the 36×36 fixture first. A later separately admitted run can use 128×128; do not chain cases automatically.

## Transaction and stopping rules

1. Read all ten advertised bitmap slots; abort without writing if any is present. Recheck the selected last slot immediately before upload. This conservative test gate does not change V1's production slot policy.
2. Record upload intent before method 3; require correlated ACK and presence check.
3. Bind one carousel element's icon field to the test bitmap, with no text references. Select model 0x6d and commit. Start the **30-second** observation only after these ACKs. Read-only presence checks drain the transport during the window.
4. Withdraw focus and commit, then restore the exact saved factory Carousel body and commit. Only after every detachment/restoration ACK, delete the specific tracked bitmap and check it absent.
5. A lost upload reply still triggers cleanup of the tracked slot. Uncertain graph restoration retains the bitmap and reports incomplete cleanup; no whole-session disposal or blind retry.
6. Visual absence and normal V1 return are separate operator checks. No protocol result marks a visual pass. The 30 seconds bounds the host observation window, not a receiver TTL: loss of the computer or connection can leave graphics until recovery. Manual iDrive restart recovery must already be verified. This experimental runner has no automatic factory-priority watcher; keep factory controls closed and remain parked with the operator watching throughout. It must not be installed persistently or tested while driving. Do not unplug or proceed to another case on incomplete cleanup.

The runner does not automate V1 pause/resume. Use the existing [V2 car-test procedure](V2-CAR-TEST.md) and verify the unchanged installed baseline after the test. If an exception leaves a rendered frame or uncertain reference, remain parked and use the established recovery procedure before V1 resumes.

## Offline checks

- 39 real captured model bodies re-encoded exactly (27 Carousel, 12 Voice).
- Codec malformed-length, identity and variant checks; strict Boolean and disposal replies.
- Transaction fault injection: occupied pool produces no writes; lost upload ACK remains tracked; exact restoration precedes deletion; failed restoration prevents deletion; cancellation runs cleanup; wrong snapshot rejected before protocol I/O.
- IU/cross image fixtures retain exact BGRA/RLE32 round trips.

Outstanding vehicle evidence is custom bitmap acceptance, observed placement/size, and visible cleanup. Offline code does not answer those receiver questions. Current-session admission must be established before calling a car session ready.
