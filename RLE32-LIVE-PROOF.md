> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# RLE32 custom drawing and removal: live proof

On 16 November 2026, the parked Supra displayed our generated white rectangle
and cross in **both the windshield HUD and gauge cluster**. The driver confirmed
that both displays returned to normal after cleanup and that factory radio,
navigation, HUD and iDrive still worked. The cluster acknowledged all withdrawal
steps, acknowledged deletion of our bitmap, and then reported it absent.

This proves a custom bitmap path through the **shared factory navigation road-icon
model**. It does not prove an independent overlay, windshield-only routing,
continuous tachometer updates, coexistence with active navigation, or persistence
across sleep/startup. The test also displayed a built-in roundabout symbol and
navigation information; those are not part of the custom bitmap.

## Working graph

Service B006/interface1 on the cluster at 160.48.199.96:30502, reached through
an authenticated SSH forward from the head unit. Shared handle200 is preserved:
we never send instance-dispose method7. An earlier distinct-app create using
profile BMW.IC.Guidance returned this same factory handle and configuration.

- Method3/tag2 bitmap resource: type1, selected unused slot0x01000009,
  negotiated dimensions150×36, RLE32 stream.
- Method14/tag2 coming-road list: model type40, selected ID0x27000004,
  one resource-list entry referring to our bitmap.
- Method10/tag1 description: model type15, ID0x0f000004, coming-road reference
  to that road list, with current-state thresholds and distance support models.
- Shared maneuver list/type32 and list-state/type33 select the description;
  initialization and destination/route-position information complete the trial.
- Model34 thresholds, model29 distance and model17 destination information
  use measured field values from a retained factory stream. The runner remaps
  support model IDs into their advertised high slots. It does not replay the
  entire route or upload factory text resources.

The minimal picture/description graph showed nothing. Adding support models
showed a built-in roundabout circle. Adding the road-icon bitmap reference then
showed the **rectangle/cross**, confirmed by the driver in both displays. This
comparison is why the working path is identified as the road-icon list rather
than assumed to be the high-roundabout picture field.

The description wire order is coming-road ID **before** current-state ID.
Earlier codec labels were reversed; corrected with the support-model trial.

## Encoder evidence

`tools/ric_rle32.py` takes tightly packed BGRA pixels and emits the firmware's
count-prefixed A,R,G,B tuples. Repeated runs set bit7; counts are1–127. Literal
runs are buffered, with the original final-single-pixel behavior retained.
The stream is zero-padded to the **next** eight-byte boundary, including a new
block when the tuple bytes were already aligned. There is no PNG header or
per-row reset. The 150×36 test marker encodes to872 bytes.

This was not inferred from a generic format name. The original ARM routine in
captured NavigationFully was executed offline under an emulator, with only its
vector-append call replaced by a byte collector. All24 inputs, including long
runs, random pixels and the complete marker, matched the new encoder exactly.
Firmware SHA256:
`957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d`.

Key addresses: compressor0x8a1040, literal buffering0x8a0d80,
final literal0x8a0e80, repeated tuple0x8a0f5c, byte packing0x8a0c88,
final flush0x8a0c00. The emulator harness and traces are in the private Drive
archive; OEM binaries are not distributed with this source.

## Cleanup evidence and limits

Resource-only trial: absent → upload acknowledged → present → disposal
acknowledged → absent. No display binding was sent in this first stage.

Successful visible trial: cancel/idle, empty maneuver list, absent high-picture
reference, initialize, empty custom road list, restore stopped destination info,
then dispose **only** our bitmap and check it absent. All seven graph-withdrawal
steps and bitmap disposal were acknowledged. All32 request packets and replies
are retained. Driver confirmed marker removal and normal factory behavior.

An earlier minimal trial encountered the cluster's idle magic cookie
`ffff800000000008deadbeef01010200`; the transport had only recognized its other
observed form. This displaced reply matching in the initial cleanup report.
The saved packets were reconciled by method/client/request ID, and a fresh
connection confirmed resource absence. Both exact cookie forms are now handled
and regression-tested. Raw failure evidence was retained, not rewritten as a
clean run.

Shared-session resource checks are **not locks**. Highest advertised slots are
not private allocations. This trial requires factory guidance stopped and does
not solve concurrency with the factory renderer. It must not run automatically
or while driving. Process/cable/power loss can still prevent cleanup; a closed
socket is never treated as proof of erasure.

## Reproducing the bounded test

The Mac-side runner requires Python3, existing verified SSH access, a saved
successful create reply and the retained factory support stream. It defaults
to a no-network plan. Example with operator-supplied paths/current SSH master:

```sh
python3 tools/run_shared_roadicon_trial.py --execute \
  --create-response "$CREATE_REPLY" --support-stream "$SUPPORT_STREAM" \
  --ssh-socket "$SSH_MASTER" --head "$HEAD_IP" --output "$NEW_RESULT_DIR"
```

The exact evidence files used are in the private archive:

- `car-drawing-trial-2026-11-16/profile-probe/001-response.bin`
- `car-session-consolidated-2026-11-16/navigation-cycle/recording-7740ddd3/stream-007.bin`

Park outdoors, keep the engine idling with the HUD visible, stop factory guidance
and let the radio selector close. The marker window lasts15 seconds; cleanup
runs automatically. Visual observations are recorded separately by the operator
so the runner never promotes protocol ACKs to visual proof. Check both displays,
resource absence and factory functionality before unplugging.

The packaged runner was exercised against a local transport stand-in using the
same evidence inputs: all32 emitted requests matched the successful live run
byte-for-byte. Full Python suite:201 tests passed. No further vehicle commands
were sent during packaging.

## Next app work

Replace the marker with a tachometer bitmap and establish update performance;
remove unwanted built-in navigation symbols; determine usable placement/colors;
and design explicit arbitration with factory navigation. Independent-session
allocation and windshield-only routing remain unresolved. The proven display
size is150×36, not a full-screen drawing surface.
