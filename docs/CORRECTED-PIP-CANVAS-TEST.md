> Executed: see [19 November live results](CORRECTED-CANVAS-LIVE-2026-11-19.md). Custom native pixels appeared in the cluster, not the windshield. Prepared helper below is superseded by the session-counter fix.

# Corrected native HUD-profile canvas experiment

Prepared offline on 19 November 2026. This is an executable, bounded experiment; it is not yet evidence that V2 can occupy the larger windshield area. V1 is unchanged. No Hz tests or paid firmware access are required.

## What changed from the failed marker

- The owned source is 277×160, the captured HUD8402 geometry, inside an800×480 backing. The earlier320×200 was an arbitrary marker choice.
- Metadata now comes from executed native HUD construction and verified BGRA conversion. HUD record byte7 / framebuffer byte4 is0, not the old G30 template's1. Day/Night is explicit and derived from captured style parameters.
- The producer obtains its own B009 lease and acknowledged selection1 before creating any Screen window. Selection1 is a cluster request, not a windshield grant. No fabricated HUD0 selection or factory endpoint reuse.
- LayerManager's actual routing table maps factory1056 to Screen display index1. Its unknown-owned-window fallback preserves an explicit OTHER2 assignment for experimental window268444457. The test does not borrow1056 or alter the table.
- A private go signal starts the full30-second viewing interval only after the graph is configured. Setup and drawing use a45-second deadline. A blocked native IPC call or missing cleanup output remains unknown and requires recovery; timer expiry alone is not removal proof.

The remaining live question is whether this corrected source, metadata and negotiated graph associate the marker with windshield pixels. A turn arrow, completed handshake or present resource does not answer it. The marker is a white border/cross with asymmetric colored corners; observe both windshield and cluster.

## Preparation and admission

Use the exact current-V1 pre/post procedure in `B006-HIGH-BITMAP-CANDIDATE.md`. Capture and verify all15 current files, preserve runtime/fault state, cooperatively stop V1 and confirm both displays clear. No persistent enabled-token, lockout, startup file or V1 binary changes are part of this experiment.

Read current addresses/interfaces and service offers. Bind the helper only to an existing head-unit address; do not configure an alias. Retained B009 TCP port is30503. Retained SD traffic identifies receiver160.48.199.96, port30490, and factory HU source160.48.199.119; verify that source is still assigned before binding. Do not invent or configure a copied G30 source address. The receiver accepting our distinct owned subscription endpoint is a live admission check; if it does not acknowledge, the helper must exit without creating Screen output. Keep guidance and radio closed.

Before staging, verify no old experimental producer or window268444457 exists and that OTHER2 is empty. The helper independently requires OTHER2,800×480, no windows/scene, and V1 STOPPED with no factory socket/handoff marker. It rechecks V1 while running. Abort on unknown state.

Stage only the new helper in a fresh root-owned0700 directory named `/tmp/supra-pip-corrected-<16-to-32-lowercase-hex>`. Record its local and remote checksum. It accepts:

```
corrected-marker --parked-experiment 251658244 day RUN_DIRECTORY PRODUCER_IP RECEIVER_IP SINK_PORT SD_PORT
```

The host runner takes reviewed JSON argv arrays for launching that helper, creating its empty `go` file, and creating its `stop` file. Those operations target only the fresh directory. It uses an existing owned loopback forward for B006; neither runner installs anything.

```
python3 tools/run_corrected_pip_trial.py \
  --create-response /private/kit/create-response.bin \
  --support-profile /private/kit/supra-profile.bin \
  --style day --output /private/session/corrected-day
```

That command only writes an offline plan. Live execution additionally requires `--execute`, `--v1-pre`, `--v1-paused-and-displays-clear`, `--guidance-stopped`, `--local-port`, `--producer-argv`, `--go-argv`, and `--stop-argv`.

The runner verifies the exact producer contract and owned sink confirmation, configures the graph, sends go, then announces WATCH NOW after the helper confirms the visible window started. Record for the full30seconds. Do not interpret the factory turn arrow as our image.

## Removal and V1 restoration

Stop the owned pixel producer first. Require local window/context cleanup and unsubscribe-sent confirmation. Then withdraw guidance references, restore stopped destination information, dispose only the attempted PiP resource and verify absence. An uncertain cleanup stops further tests. A sent unsubscribe is not a remote-image-removal acknowledgment; the separate B006 cleanup and visual check are required.

Confirm all graphics are gone. Use the established normal iDrive restart to resume installed V1. Verify it is visible/updating and collect the15-file post capture plus runtime evidence. Never reinstall an older V1 package to satisfy a stale hash pin.

The companion detailed-picture paired test in `B006-HIGH-BITMAP-CANDIDATE.md` uses the already-proven inline bitmap transport and tests a separate image slot. It does not share the native helper or require a PiP window. Run it only after complete cleanup, within the same session if needed. No menu-cell substitutions or Hz runs are included.

## Offline validation limits

Native instructions establish metadata construction, channel order, style parameters and LayerManager routing/fallback. QNX compilation establishes ABI/link compatibility. Real local socket/subprocess checks exercise handshake refusal and graph cleanup, not a simulated renderer. The physical receiver and visible size still require the actual car.

Prepared helper SHA-256: `5fe8038885e8af6d85c4136bc420e76905759d25012c856af4384157b965d504`. Final offline suite:56 PiP tests,3 corrected-contract tests,4 detailed-picture tests, plus three socket/subprocess orchestration cases. QNX ARM build and dependency audit passed. No vehicle execution occurred.
