# New car batch: activate the 408×132 windshield test surface

Two bounded experiments are ready for the reference car: a dim RGB surface and the factory grid/circles pattern. These activate `hud_TestBmp`, not V1's road-icon strip. No car connection occurred during preparation. Installed V1 files are untouched; the owner deferred runtime restoration at the last session.

**What this batch can establish:** whether the installed receiver exposes the traced larger HUD test surface through diagnostic routine A102, and whether it visibly occupies greater height than V1. **What it cannot establish:** arbitrary uploaded-image access, an enlarged road-icon viewport, or persistent application use of that area. Do not call a factory pattern a completed custom-canvas unlock.

## External activation is now traced

The private auxiliary receiver image `swfl_00005ffb` 004.000.003 contains the actual routine registration and handler. `verify_hud_diagnostic_surface.py` executes its native startup data initialization, revealing registration entry88 at RAM 0x1d5a8+88×16:

`31 00 02 a1 00 00 00 00 01 00 00 00 00 00 00 00`

This registers SID31, routineA102, dispatch class0, minimum session1 and no security requirement in this table. The jump table at0x10f4008 maps class0 to0x10f4022→0x10f6146. Do not infer target addresses from firmware addresses.

Native request flow:

1. `0x10f84be` parses the service payload `[subfunction,A1,02,parameters...]`; `0x10f3fd0` validates the initialized registration and dispatches it.
2. `0x10f6146` copies the complete service payload into an asynchronous descriptor through `0x1031ad4`. Descriptor+0 is little-endian routineID, +2 subfunction, +3 complete service payload, +6 parameters, +0x68 payload length. This explains the otherwise misleading three-byte gap before parameters.
3. Scheduled callback `0x1037c50→0x10ec968` selects A102 and reaches `0x10ecad2`. Start accepts exactly four parameters; stop accepts none.
4. `0x102cce8` writes the five-byte control at RAM0x4a28. Producer `0x1072adc` reads it via0x1028684 into group0x31/field0. Sender0x1062482→0x106ced0 emits internal record0x16e.
5. The [renderer input trace](RECEIVER-SCENE-CONTROL-2026-11-20.md) carries that record to event0xac and `TestBmpHUD`, whose two scene nodes have408×132 bounds.
6. The response travels through0x102cade→0x10f638e and the asynchronous completion path. Native execution verifies the response status alongside the actual control bytes.

The native A102 handler requires operating-state byte at0x3fb8 >=7 for **both start and stop**. This state comes from a received message's byte6 low nibble through0x10d6b52→0x10267f2; its full vehicle-state meaning is not established. Do not spoof it, bypass rejection, or change ignition during a test. There is no proven ECU-side timeout. Host cleanup is bounded, but cannot guarantee removal after cable loss, host failure or a state change.

## Exact tests and inverse

| Case | UDS request | Expected positive reply | Result in older native handler |
|---|---|---|---|
| Dim RGB | `31 01 A1 02 00 10 20 30` | `71 01 A1 02` | selector0, RGB16/32/48, enable1 |
| Grid/circles | `31 01 A1 02 5C 00 00 00` | `71 01 A1 02` | selector0x5c, factory grid/circles, enable1 |
| Stop | `31 02 A1 02` | `71 02 A1 02` | `[0,0,0,0,2]`, disabling both HUD test nodes |

Selector0 uses a solid brush. Selector0x5c resolves to `Imports#hud#hud_TestBmp#0x5c_m15_grid_and_circles`. No uploaded IDs or V1 bitmap resources are touched. The renderer verifier now executes the **actual enable2 branch** at0x296c12 through0x296ec0 to0x296ece, confirming both visibility flags clear.

The installed receiver is **008.000.000**, while the offline executable is **004.000.003**. Compatibility is an explicit live hypothesis. This test pins the previously captured installed ECU60 F197 and F101 replies; it does not pretend the installed firmware matches the analyzed image. It requires an exact positive stop reply before any start. A rejection, identity mismatch or unexpected response ends the attempt; no session change, unlocking, reset, coding or fallback routine is permitted. Positive stop is an admission check, not proof that every 008 internal behavior matches004.

## Parked session procedure

1. Use the established current V1 preflight/cooperative pause procedure in [V2 car test](V2-CAR-TEST.md). Capture and verify all15 current installed files with `verify_current_v1_test_baseline.py`. Require CLEAN/STOPPED, no worker/broker ownership, navigation stopped, radio selector closed and normal displays. Keep the existing normal recovery procedure available. Do not replace installed V1 files.
2. Retain one fixed camera framing that includes the known V1 footprint before pause. The new tests must show top/bottom extent beyond that footprint; changed camera zoom or horizontal length alone is not evidence of increased height.
3. Run RGB first. The runner checks live V1 stopped state through the established SSH master, reads the pinned receiver identity, requires stop ACK, then announces **WATCH NOW** after start ACK and holds30seconds. It always attempts stop after a start attempt, including a lost start reply or interruption.
4. Require stop ACK **and visually normal displays** before running grid. If RGB fails or remains visible, do not run grid. A full-area color that shows only the old strip is a failed extent result; do not repeat it.
5. Run grid once for30seconds. Photograph top/bottom/left/right pattern extent in that same framing. Record windshield and cluster separately; cluster-only output is not windshield success. Optical eye-box clipping is separate from software dimensions.
6. Require final stop ACK and both displays normal. Take a new15-file capture and verify it against the pre-capture. Restore V1 with the established normal restart only if requested; record whether restored or intentionally left paused. Do not report runtime restoration from file hashes.

From the repository root, set the following to the **current session's verified** values. No network discovery or guessed default addresses are built into this runner:

```sh
python3 tools/run_hud_diagnostic_surface.py

python3 tools/run_hud_diagnostic_surface.py --execute --case rgb \
  --gateway "$GATEWAY" --source-ip "$SOURCE_IP" --interface "$ENET_INTERFACE" \
  --head "$HEAD_IP" --ssh-socket "$SSH_MASTER" \
  --v1-pre "$CURRENT_V1_PRE" --stationary-v1-paused --output "$SESSION/rgb"

# Only after stop ACK and visual clearance:
python3 tools/run_hud_diagnostic_surface.py --execute --case grid \
  --gateway "$GATEWAY" --source-ip "$SOURCE_IP" --interface "$ENET_INTERFACE" \
  --head "$HEAD_IP" --ssh-socket "$SSH_MASTER" \
  --v1-pre "$CURRENT_V1_PRE" --stationary-v1-paused --output "$SESSION/grid"

# Recovery only: never starts anything; works without V1/identity preflight.
python3 tools/run_hud_diagnostic_surface.py --execute --cleanup-only \
  --gateway "$GATEWAY" --source-ip "$SOURCE_IP" --interface "$ENET_INTERFACE" \
  --output "$SESSION/cleanup-retry"

python3 tools/verify_current_v1_test_baseline.py \
  --pre "$CURRENT_V1_PRE" --post "$CURRENT_V1_POST"
```

Every output directory must be new. The runner records raw HSFZ frames and timestamped request, identity, viewing and cleanup events with flushed journals. Cleanup retries at most3times on fresh connections. A missing stop ACK blocks the next test; keep the connection and ignition stable while resolving cleanup. Never assume unplugging clears the pattern.

## Offline checks and limits

Seven native cases pass: RGB start, grid start, stop, start and stop below the state threshold, malformed start length and unsupported subfunction3. The code executes firmware data initialization, real registration lookup, parser, dispatch, record copy, application handler and response completion. Only OS critical-section enter/exit and event notification are stubbed; asynchronous scheduling is advanced manually. Session and operating state are synthetic. No security or application condition is patched. HSFZ and physical display behavior are not emulated by that verifier.

Host regression checks cover normal completion, stop rejection before start, lost/rejected/mismatched start replies, interruption, failed cleanup retries, successful retry, request allowlist and no sockets in default mode. The existing renderer verifier pins scene bounds and all256 selector inputs; the enable2 withdrawal branch passes without instruction substitution.

Uploaded-image research remains separate: this widget accepts RGB or named factory assets, with no uploaded resource-ID argument in its verified control record. This batch will establish external reachability and usable physical extent, giving a real larger destination to investigate without repeating the strip tests.
