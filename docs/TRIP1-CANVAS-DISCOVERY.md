# Supra full-HUD canvas discovery: two-trip strategy

**Reference:** 2026 GR Supra J29, NBTevo_T24081I, QNX 6.5 ARM32; V1 installed/accepted, exact baseline dated 2026-11-18. Existing repo is `bryanmishkin/supra-native-hud`. This kit is new host-side offline / read-only tooling. **No car connection was performed to prepare it.**

## Goals and decisions

**Trip 1: discover *every observable available HUD drawable/resource family*, route to physical target, and run one limited 320x320 PiP drawing smoke test only if the PiP serializer, attachment and cleanup have been independently verified.** Gather enough unique observations to design the second trip without going back for generic captures.

**Trip 2: targeted drawing and clipping/position tests for each candidate genuinely supported surface**, after Trip 1 analysis provides safe semantics and ownership. Do not infer one full-frame canvas simply from a displayable size, image resource limit, factory HUD-height rectangle or screenshot.

For Trip 1 the most important evidence is **time-aligned physical HUD state**, local displayable buffers and message/model transitions, and the full negotiated resource set. No network/messaging sent during stage captures. V1 is the known-good **control**, and must not be reinstalled, disabled, patched, or overwritten for discovery.

## What is already done (do NOT repeat)

- 112 MOST entries and 52 FBlocks parsed in baseline/radio/navigation; HUDTerminal 0x82 not advertised in those windows.
- Working V1: bitmap type 1, 150x36, B006 method 3 variant 2, visible coming-road/method14 binding, current slots 0x01000008/09, factory takeover and cleanup.
- Actual shared B006 handle 200 profile: 22 entries; PiP type 2, config tag 35, 320x320 fields, slots 0x02000000..04. Create response SHA256 `2740bccc5fc25fd6bc983ecd69fc98792ad1c073e220a4a3c1c23f3bc12f676e`.
- Saved 99 unique paired source snapshots across seven GV displayable IDs 1/3/7/9/11/17/19. ID 9 and 11 first-chunk PiP data encode 800x480 and 480x431 pairs, but *source dimensions / viewport / physical sink are not yet established*.
- Factory B006/B009/B00E traffic captures and static NavNBTEvoController / NavigationFully builds already archived; no B006 method-3 variant-3 PiP upload in those recordings. Existing original session launchers and baseline recoveries are retained; don't rerun unrelated tests.

## Offline gates before car hookup

1. Use the exact archived V1 installation/rollback kit; ensure its hashes and known-good factory behavior can be checked without modifying it. Bring backup files and a known normal recovery procedure. Do not clear previous fault records.
2. Verify that `tools/canvas_stage_capture.py` and `tools/canvas_stage_diff.py` pass host tests and default to no-network plans. They require only Python 3 and the existing `tools/capture_runtime.py` (SSH command line/known-host checks).
3. Verify `tools/canvas_resource_presence.py` against the actual saved `car-drawing-trial-2026-11-16/profile-probe/001-response.bin`; its only SOME/IP method is B006 **2** (read-only check). It refuses all other resource ranges and has no create/upload/dispose/initialize capability. It uses the existing `tools/ric_live_trial.py` `TcpExchange` to correlate replies and retain original wire packets.
4. **PiP DRAWING GATE**: the test is *not yet executable* merely because slot presence reads work. Decode and review the exact PiP method-3 **variant-3** payload, generated from the captured ARM serializer `0xBB51E8 -> 0xBB5158`; decode the visible `setPIPElementForICHUD`/`sendAttachToCommandPIPICHUD` method and explicit reference/position/size fields; determine the bounded rollback/clearing sequence; host-test valid/invalid/cancel/timeout response handling. Only then build a new **separate default-disabled PiP marker sender** with operator confirmation. No V1 code changes. **If any gate fails, do the five method-2 presence checks only and label the first-trip PiP draw `NOT RUN`, without guessing.**
5. Bring the **already built, audited QNX ARM** `supra-continuous-capture-qnx` and its verified SHA256. This source-only kit does not contain or substitute that OEM/target executable, SDK, private kit or authorization credentials. Preserve existing PCAP validation and no-drop gates. Do not compile C code for the first time while connected to the car.


## Additional discovery already recovered offline from raw PCAPs

New offline, bounded decoder: `tools/canvas_sd_inventory.py`. It reads the PCAP records and the SOME/IP-SD UDP 30490 messages, checks all packet/entry/option boundaries, associates each service to referenced endpoint options, and emits service/instance/host/port inventories. It transmits **nothing**. The live recorder already retains these UDP messages, so there is no need to build a separate network service scanner.

- **Engine-start**: 5,610 PCAP packets, **3,539** SOME/IP-SD packets, **127 advertised service/instance pairs**, zero malformed.
- **Navigation-cycle**: **3,828** SOME/IP-SD packets, the **same 127 advertised service/instance/host combinations**, zero malformed.
- Advertised B006 guidance at 160.48.199.96:30502; B009 DisplaySink at 160.48.199.96:30503; B00E list at 160.48.199.96:30502. These confirm known V1 endpoints against independent service advertisements.
- Other cluster-side services advertised at **160.48.199.96**: B00A and B011. Other services at **160.48.199.97**: B001, B002, B003 and B007. Another B00C is hosted on the **head unit .119**. Interface names/graphics capabilities are unverified for these entries. **Do not transmit arbitrary SOME/IP calls or call any service a drawable canvas from advertisement alone.**
- Trip 1 should preserve this broader service inventory for *every* PCAP, check for new/different offers under alternate factory modes, and correlate only relevant changes with synchronized visual observations. Do not repeat the 127-service decoding effort by hand.

Offline command for an existing or newly recorded PCAP:

```bash
python3 tools/canvas_sd_inventory.py "$PRIVATE_OUTPUT/recording/traffic.pcap" \
  --output "$PRIVATE_OUTPUT/recording/someip-sd-inventory.json"
```

The current recorder's known-peer TCP/UDP filter and service discovery multicast are sufficient to observe these advertisements, **but not guaranteed to capture arbitrary unknown unicast graphics protocols on different peers**. New networks/interfaces found by `ifconfig` or service metadata require a separately reviewed wider passive capture, not silent firewall/routing changes.

## First-trip operator sequence (parked, no driving)

- Park safely. Ensure V1 is healthy and normal speed/limit/radio/HUD output is observable. If V1 has a fault, collect existing persistent diagnostics first and avoid experimental drawing.
- Establish existing reviewed ENET/SSH connection and use current verified `--head`, `--local`, `--known-hosts` and (if needed) `--socket`. Scripts never enable SSH, restart processes, change coding or change the HUD. All manual menu actions belong to the owner.
- Start the previously built **120-second non-promiscuous internal VLAN73 recorder** using `tools/consolidated_capture.py --execute --record-only ...` (see `STARTUP-AND-CONSOLIDATED-RUNBOOK.md` for the exact validated command). **Do not begin manual actions until its `recording_ready` output appears.** Record host-clock markers with `tools/capture_mark.py`; annotate the same states in phone video/photos of the *physical projected HUD* with relative time/position. A later stream comparison alone cannot prove which graphics were on the windshield.
- Capture discrete **stage snapshots**. Set the physical display first, then execute `canvas_stage_capture.py` for that stage. Plan multiple PCAP windows rather than cramming every stage into one 120-second run. Do not turn HUD options on/off while a stage snapshot is underway. Suggested sequence: `baseline`, `hud-calibration-visible`, `hud-height-bottom`, `hud-height-middle`, `hud-height-top`, `hud-calibration-hidden`, `radio-open`, `radio-closed`, `speed-limit-visible`, `speed-limit-hidden`, `navigation-visible`, `navigation-hidden`, and `pip-graphic-visible` **only if genuinely available through stock UI**. Skipped states are marked **unavailable**, not faked or invented. Ensure factory warnings/assistance displays are preserved, not suppressed.
- Each stage probe enumerates **all currently listed** `GVCommand_*` objects in `/opt/nav/eceusa/bin`, not a hard-coded list of seven IDs, hashes and reads each up to three times, retains full bytes and first-chunk metadata, and records network/process/service inventory. A changed first chunk or new displayable ID is a *candidate* link; it does not alone establish final physical compositing surface. The read-only `dd` captures are not atomic and may contain stale/reusable buffers.
- Run the separate **read-only PiP occupancy probe** during a quiet factory state, with original `001-response.bin`, against all five PiP resource IDs. If any reply fails, stop that probe and keep the raw packet. Presence=false is not an ownership lock; presence=true means do NOT overwrite the resource. Check no factory messages or HUD elements were affected.
- **Conditional PiP 320x320 marker test:** only if the offline drawing gate was closed *before the car trip*, the selected PiP slot is confirmed absent, the factory drawing state is safely idle, the exact resource reference and display destination are known, and removal/absence/visual checks are runnable. Test a **small static marker** inside a 320x320 resource (not a 320x320 full-screen takeover), explicitly remove it and verify the factory HUD normal. If no verified sender exists, **do not run a trial**; preserve the first-trip discovery result for Trip 2.
- End by checking normal V1, radio/nav, speed/limit/assistance views, gathering artifacts, comparing clocks and hashes, confirming recorder cleanup and no unexpected processes. Do not alter persistent V1 install tokens.

## Host examples (dry-run first)

```bash
python3 tools/canvas_stage_capture.py
python3 tools/canvas_resource_presence.py
```

For each owner-confirmed stage, replacing values from current connection preflight:

```bash
python3 tools/canvas_stage_capture.py --execute \
  --stage hud-height-top --note "factory calibration rectangle visible; high projection" \
  --head "$HEAD_IP" --local "$LOCAL_ENET_IP" \
  --known-hosts "$KNOWN_HOSTS" --socket "$SSH_MASTER" \
  --samples 2 --output "$PRIVATE_OUTPUT/hud-height-top"
```

Read-only PiP slot availability (not a drawing command):

```bash
python3 tools/canvas_resource_presence.py --execute \
  --profile "$EXTRACTED_PRIVATE/001-response.bin" \
  --head "$HEAD_IP" --ssh-socket "$SSH_MASTER" \
  --output "$PRIVATE_OUTPUT/pip-presence"
```

After the trip, locally compare all stages:

```bash
python3 tools/canvas_stage_diff.py "$PRIVATE_OUTPUT"/baseline \
  "$PRIVATE_OUTPUT"/hud-height-bottom "$PRIVATE_OUTPUT"/hud-height-top \
  "$PRIVATE_OUTPUT"/radio-open --output "$PRIVATE_OUTPUT/canvas-diff.json"
```

The current probe **does not implement** network capture on its own. Run the existing recorder concurrently as above. The current probe also does **not** decode and live-send the 320 variant-3 PiP payload.


## 320x320 drawing-test fixture prepared (offline only)

`tools/canvas_pip320_marker.py` generates an **opaque 320x320 BGRA marker**, plus a PNG reference preview and SHA256 manifest. The marker is deliberately asymmetric: different-colored corner blocks, a five-pixel inset white border, central cross and calibration tick marks. It is suited to observing orientation, clipping, scaling, and placement once a separately validated type-2 PiP serializer/ICHUD binding exists.

```bash
python3 tools/canvas_pip320_marker.py --output "$PRIVATE_OUTPUT/pip320-reference"
```

**Important:** The generated BGRA bytes are *not* a valid B006 PiP variant-3 payload by themselves. The new tool does **not** upload/draw anything and will not be substituted for an unreviewed on-car sender. Before the first trip, a 320 test is permitted only after variant-3 content encoding, on-screen binding, factory priority and verified cleanup pass the previously described gates. Otherwise take the read-only presence evidence and defer live drawing. The second-trip design can use the same marker across other supported surfaces after each contract is established.

## First-trip evidence acceptance matrix

| Question | Required evidence | If missing |
|---|---|---|
| Which drawables are listed in this mode? | Hash-verified per-stage `GVCommand` directory + exact bytes, new IDs compared with baseline | Label stage incomplete, not zero canvases |
| What did the windshield show? | Operator-confirmed state + synchronized video/photo | Geometry and source/destination remain unknown |
| How did factory routing change? | No-drop B006/B009/B00E packets, request/reply sequence and timestamps + manual markers | No causal conclusion |
| Were new resource families available? | Current negotiation or validated cached profile, type/tag/count/offset/limits and current checkResource Boolean where read-only | Keep availability unresolved |
| Is 320x320 drawn and cleaned? | ACKs for correct variant-3 upload and ICHUD binding, confirmed visible marker, reference removal, resource dispose, post-dispose absence, normal factory displays | `NOT RUN` / `FAILED`, never assume success |
| Can the full logical HUD be addressed? | Proven active ICHUD compositor bounds, coordinates, clipping and no interference with required factory warnings | Full-canvas not proven |

## Second-trip candidate tests

Build separate bounded drawing trials **after** Trip 1 analysis assigns exact resource, model and sink; test PiP, SVG/vector, image/bitmap and any other negotiated resource classes one by one, with a separate isolated test and cleanup for each. Do not assume model types or factory speed-limit graphics are writable canvases. Prioritize an independently compositable region and geometry map, not overwriting the physical entire HUD.

## Safety and fidelity

- All new stage and presence probes are read-only. A V1 background worker and factory interface must never be killed/disabled as a discovery shortcut.
- A successfully registered service or empty resource slot does not authorize displaying graphics. B006 checkResource reply semantics are resource presence, not exclusive locks.
- Do not turn the car's camera, radar, speed and speed-limit, collision warnings, or navigation safety messages into targets for experimental overwrite.
- The owner must remain parked for any visual drawing test, with a known normal way to restore factory displays; uncertain cleanup is a stop condition, not a cue to try the next resource.
- Keep private logs, OEM binaries, location traces and factory software out of GitHub. Publish only generalized evidence and the source-only tool files.