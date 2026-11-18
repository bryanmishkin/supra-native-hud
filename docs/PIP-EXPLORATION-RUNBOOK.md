# Factory routing and pixel-binding capture

Status: offline-prepared exploration, not a working larger-display fix. No author contact. V1 stays installed and running. No test images, synthetic navigation, SD subscription, layer setters, coding, or startup changes.

## Preparation

Use Python with pyelftools installed (the existing analysis environment already has it). Use the supplied capture binary with SHA256 `fc0ee3c1c275ba75dd3ee64402e5b4747d5e7a3454e34c1c318d83df2e045ea6`; its ARM/QNX ABI audit is packaged alongside it. It is the previously captured/tested recorder, not a new untested producer. Verify the kit's SHA256SUMS before use.

At the parked car, verify SSH host identity, actual ENET local/head addresses and V1 health. Use existing verified SSH access; this runner does not activate SSH. Confirm a **normal factory HUD navigation display option** exists and record its original value before changing it. If absent, stop this experiment: record the menu evidence and do not substitute coding or a guessed selector. Start factory guidance, leave radio closed. Record whether the route instruction is visible in windshield and cluster separately. No driving is needed.

Set these shell variables to verified session values: `PY` (Python path), `HEAD`, `LOCAL`, `KNOWN_HOSTS`, `KIT` (absolute kit directory), `OUT` (new absolute evidence directory). Run from the extracted source repository root. The recording output must be fresh. Optional existing SSH control socket can be supplied to both commands with `--socket`.

```sh
"$PY" tools/pip_exploration.py before --execute --head "$HEAD" --local "$LOCAL" --known-hosts "$KNOWN_HOSTS" --output "$OUT"
```

Stop on a nonzero exit or any baseline mismatch. In a dedicated terminal start:

```sh
"$PY" tools/consolidated_capture.py --execute --record-only --head "$HEAD" --local "$LOCAL" --known-hosts "$KNOWN_HOSTS" --output "$OUT/recording-session" --binary "$KIT/supra-pip-passive-capture-qnx" --sha256 fc0ee3c1c275ba75dd3ee64402e5b4747d5e7a3454e34c1c318d83df2e045ea6
```

Wait for `recording_ready`, then set `RECORDING` to the exact folder printed. Do not begin timed phases before READY. Capture ends automatically at 120 seconds; bounded RAM upload/readback is the only remote write, and its removal is verified. It records TCP/UDP involving cluster addresses .96/.97 plus UDP service discovery on vlan73, including control and possible pixel traffic.

## Four phases during the recording

Use a second terminal. Each phase command timestamps the **actual completed user action**, then reads the PiP surface, two LayerManager screens and two native display descriptors. Supply the real observation; do not copy a predicted outcome. Keep each phase unchanged for its minimum duration **from its timestamp**, including the time spent reading snapshots.

1. `original`: original menu value, guidance active, hold at least 20 seconds.
2. `hud-nav-off`: user disables only the factory HUD navigation display option, hold at least 20 seconds.
3. `hud-nav-on`: user enables that same option, hold at least 30 seconds.
4. `restored`: user restores the exact original option value, hold at least 10 seconds.

For each phase, set `PHASE` to the name above and `OBSERVATION` to the original/current menu value and actual windshield/cluster appearance:

```sh
"$PY" tools/pip_exploration.py phase --execute --head "$HEAD" --local "$LOCAL" --known-hosts "$KNOWN_HOSTS" --output "$OUT" --recording "$RECORDING" --phase "$PHASE" --observation "$OBSERVATION"
```

The total minimum observation is 80 seconds, with 40 seconds available for actions and overhead. If the user needs longer, finish restoration and preserve the incomplete result; do not hurry them or overwrite markers. A fresh bounded recording can be made while still connected. An absent option or unchanged routing is a useful negative result, not a reason to repeat the old arrow test.

## Finish before unplugging

Wait for recorder completion; verify it reports capture validity and RAM cleanup. Restore the original menu setting even if a command failed. Stop guidance and allow normal V1 return; no iDrive restart is part of this capture.

```sh
"$PY" tools/pip_exploration.py after --execute --head "$HEAD" --local "$LOCAL" --known-hosts "$KNOWN_HOSTS" --output "$OUT"
"$PY" tools/pip_exploration.py verify --output "$OUT" --recording "$RECORDING"
```

Review `exploration-result.json`, `pixel-binding.json`, recorder `inventory.json`, `result.json`, all phase snapshots and permanent V1 fault files. Compare before/after fault records: new faults require explanation even if file hashes match. Confirm with the owner that original menu state is restored, V1 updates and factory displays are normal. Save that confirmation separately. No unqualified “all captured” if phases, data integrity, descriptors or cleanup are missing.

The clock sample bounds host/vehicle offset with one-second remote resolution. Packet timestamps are vehicle timestamps; phase timestamps are host timestamps. Apply that offset interval when comparing; ambiguous boundary events remain ambiguous. Snapshot reads have their own start/end times and are not atomic.

## What the evidence decides

- B009 selection changes plus B006 native-image binding: recover exact ordering, handle/resource IDs and associated pixel streams; do not infer visible pixels from ACKs.
- Selection changes without known native bindings: isolate routing change and inspect unknown variants in the preserved raw streams.
- Only vector-navigation changes with selection 1 unchanged: this factory option does not expose the sought PiP transition in this run. Do not claim that the hardware cannot support it.
- The decoder intentionally recognizes only known native-resource/detail shapes; an empty event list is not proof that no other image mechanism exists.

This kit tests a specific factory transition. A working larger-display injection still requires a demonstrated receiver binding and a separate bounded drawing/cleanup test.
