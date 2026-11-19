# Inline bitmap in the detailed-guidance model

Offline evidence, 19 November 2026. This is a bounded candidate, not a proven larger windshield surface. V1 is unchanged.

## Transport and model

The retained B006 configuration advertises bitmap resources up to 150×36. The candidate retains that proven inline RLE32 transport and dimensions. It does not upload a larger image or create a PiP stream.

In the captured NavNBTEvoController (SHA-256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`), detailed-model builder `0xaa7c20` takes the first high-guidance chunk. It checks chunk byte 0 equals 1, obtains the picture identifier at chunk +0x18, and passes **chunk byte 1** to resource staging `0xaa7b44`. That byte selects SVG, bitmap or PiP. The value 2 stored at model +0x3d8 is drive direction; it is not the resource-kind discriminator.

The high-roundabout payload is exactly model ID, model type, maneuver type, drive direction and picture resource ID. It has no coordinates or scale parameter. `verify_high_bitmap_native.py` executes captured serializer `0xbb03dc`, including its nested integer/enum writers, and matches all 11 bytes for both reserved bitmap identifiers and the absent-reference value. Only stream snapshot/write operations are supplied by the harness. This proves serialization, not receiver rendering.

## The previously untested comparison

The historical saved-request audit found 33 directories containing the high-picture model (including offline fixtures, not 33 live sessions). Where a current-state support model was present, its third switch-distance value was 92. The recorded distance was 461. No saved high-bitmap request set in this audit used 1000 for that field. The old minimal test omitted current-state/distance references altogether. Adding support produced the factory circle; adding the road-icon reference produced the visible marker.

The paired candidate binds the same bitmap only to the detailed high-roundabout model. Its description references current state and distance, with the coming-road reference absent. Control and candidate differ only in two bytes of one double: 92 versus 1000 at current-state body offset 38. Their image, IDs, description, distance, destination information and cleanup are identical.

Native `setManeuverState` at `0xa43dc8` names the source vector `guidingStateSwitch` in its diagnostic string. Model constructor `0xa43d7c` identifies type 34 and copies that vector. `sendManeuverState` around `0xab5c80` copies its doubles sequentially and wraps tag 5 through `0xaafe4c`. The retained body contains four switch values at offsets 22, 30, 38 and 46: 10000, 3000, 92 and 70. The existing reference implementation calls the third switch GS3. Receiver-side stage selection and physical placement are not established merely by that name; the native sender proof does not execute the cluster renderer.

## Admission and interpretation

The bounded live runner has passed native sender, paired-input and cleanup review. Execution remains explicit and requires a fresh 15-file current-V1 capture; offline planning is the default. It requires V1 cleanly stopped, factory overlays closed, measured configuration, and empty reserved resource slots. Each case is static for a full 30 seconds. Withdrawal, picture-reference removal, destination restoration and exact resource disposal/absence verification precede V1 restoration.

If the close case shows the marker where control does not, the paired result supports switch-dependent selection. It does not establish arbitrary framebuffer access. If both show only a stock symbol, that rejects this particular field-change explanation; do not repeat larger images or speculative IDs. Any visible marker must be compared with the known 150×36 road-icon placement to measure whether the detailed slot actually occupies more windshield area.

## Preserve the current 19 November installation

The current resident hash is `78d463e60e399c299aaf38d608d3fd64593c0863cfd7ea88492eba730bc4e0c3`, as recorded in `V1-CURRENT-RECOVERY.json`. All other components and startup configurations retain the 18 November baseline hashes. The older V2 validator's manifest pin and the first 19 November recovery package are stale for this car: the former expects resident `7396…`, the intermediate package contains `adc7…`. Do not reinstall either to make a check pass.

`tools/verify_current_v1_test_baseline.py` has no network or target mutations. Its `--read-plan` produces the exact fixed `cat` commands and local filenames for thirteen installed components and the two active startup configurations. The operator saves successful, complete binary reads into a fresh local `pre` directory, then runs:

```sh
python3 tools/verify_current_v1_test_baseline.py --pre /private/session/pre
```

All fifteen hashes must match. Separately save the enabled token (must be `SUPRA-PERSISTENT-1` plus newline), confirm no disabled marker and that `/fs/sda0` is read-only. Save current acceptance, resident status, heartbeat, active journal and fault records. Require healthy, non-quarantined V1 with an active worker and advancing RPM frame/sample timestamps, plus the owner's visible/updating confirmation. A file match alone is not runtime health.

With guidance and radio closed, cooperatively pause the installed resident using its established `--stop /tmp/supra-hud-v1` operation. This is a runtime stop, not persistent disabling. Require `CLEAN`, then final `/tmp/supra-hud-v1/resident.status` equal to `STOPPED` plus newline and absence of both `factory.sock` and `active.jsonl.handoff`. Save the resulting journal and verify graphics are gone. Do not proceed on a timeout, quarantine or uncertain cleanup; preserve that evidence without deleting diagnostic markers.

Run the control and close cases individually, each with its own output directory and a fresh normal-display confirmation. Collect each full result before an owner-operated normal restart. A failed removal/absence check ends drawing attempts and requires normal recovery; do not attempt to reclaim unrelated factory resources.

After the normal restart, confirm visible/updating V1 and re-establish authorized diagnostic access if needed. Capture the same fifteen fixed paths into a new `post` directory and run:

```sh
python3 tools/verify_current_v1_test_baseline.py \
  --pre /private/session/pre --post /private/session/post
```

The verifier requires both sets match the current contract byte-for-byte by SHA-256. Repeat the separate runtime/token/read-only checks and confirm RPM samples advance. Archive the complete pre/post and test evidence. No install, persistent token change, V1 rebuild or rollback package write is part of this experiment.

## Exact paired commands

From the repository, first prepare each plan without `--execute`. `create-response.bin` is the retained accepted configuration; `supra-profile.bin` must pass its exact profile hash check. For live execution add the verified SSH master, head-unit address, and fresh baseline capture. No addresses are assumed by this example.

```sh
python3 tools/run_high_bitmap_trial.py --case control \
  --create-response /private/kit/create-response.bin \
  --support-profile /private/kit/supra-profile.bin \
  --output /private/session/control \
  --execute --ssh-socket /private/session/master \
  --head "$VERIFIED_HEAD_ADDRESS" --v1-pre /private/session/pre \
  --guidance-stopped
```

Only after acknowledged removal, resource absence and a normal-display confirmation, repeat with `--case close` and a new output directory. `WATCH NOW` starts the full 30-second visual interval. Record windshield and cluster separately. The decision sought is whether this detailed-picture binding displays our actual marker and whether its visible bounds exceed the existing road-icon placement. A factory arrow/circle does not pass. No Hz or RPM behavior is changed.
