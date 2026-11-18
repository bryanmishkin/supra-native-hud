> Live execution retired. See [sink-contract correction](PIP-SINK-CONTRACT-GAP-2026-11-18.md). This historical candidate did not deliver custom pixels.

# Larger PiP marker experiment

**Superseding live result:** [revision-2 test failed to display custom pixels](PIP-REVISION2-RESULT-2026-11-18.md). Only the right-turn arrow appeared. Cleanup and unchanged V1 return passed. Retain the procedure as historical; do not repeat this candidate as a ready image-binding fix.

**Current offline revision:** [format selection and producer binding](PIP-BINDING-REVISION-2026-11-18.md). Use the revision-2 kit; depth 0 replaces the earlier maximum-as-selection value 1. This remains an unproven image-delivery candidate.

**Car result:** [18 November attempt](PIP-MARKER-RESULT-2026-11-18.md) showed only a factory right-turn arrow, not the custom image. Cleanup and V1 return passed. This candidate is not a verified larger renderer.

This is an executable **parked, RAM-only experiment**, not a verified larger HUD renderer or a persistent V2 installation. It pairs a compiled QNX ARM native producer with a correlated Guidance controller. V1 binaries, configuration, enable tokens and tags are unchanged. The purpose is to observe whether this concrete pixel/model path reaches the windshield, the gauge cluster, or neither.

Credit to **ryseek** for the native Screen/APIX producer and metadata convention, and **Sq00ky / nanaisu and the Supra Android Auto contributors** for the upstream work. The scoped headers and license are in [vendor/ryseek-pip](../vendor/ryseek-pip/README.md); pinned source is `a0242e1c30d17b138845c18d6bf86ae0cd99ead6`.

## Candidate and limits

- Native backing: measured secondary Screen output OTHER2, **800×480**. No display mode, pipeline, factory window or LayerManager configuration is changed.
- Marker: **320×200**, within the decoded Supra PiP maximum of 320×320. White border/cross with cyan upper-left and orange lower-right blocks; deliberately asymmetric to identify orientation and distinguish factory icons.
- Visible opportunity: producer runs for **30 seconds total**; graph setup consumes part of the beginning. The controller prints `MARKER TEST RUNNING` after activation acknowledgements. Observe windshield and cluster separately. No RPM change or driving is needed.
- Resource: only `0x02000004`, checked absent before attempting configuration; resource type 2, selected depth 0 (reference native selection, below advertised maximum 1), packing 0 (within the retained Supra limit). Factory PiP slots 0–3 and all bitmap slots are untouched.
- Models: negotiated last detailed-maneuver model `0x07000004` and description `0x0f000004`, plus the measured V1 current-state, distance and position fields and shared list/state. These are selected slots, **not exclusive ownership**. Factory guidance and radio must remain stopped.
- Native metadata uses the reference maneuver template with the selected description identity. **That identity mapping and byte convention on this Supra are hypotheses**, not established by a successful build.
- No G30 temporary IP address, B009 subscription takeover, fabricated sink-switch event, or factory instance create/dispose is used. Existing factory sink control remains in place. Failure to see the marker is a failed routing hypothesis, not permission to force another sink or overwrite factory resources.

The measured V1 support profile is hash-pinned and copied, not edited. One synthetic test change is applied in RAM: the GS3 threshold is raised from 92 m to 1000 m, following ryseek’s native PiP setup, so the saved 461 m distance can enter the detailed-maneuver stage. Without this change the V1 road-icon fields could suppress the new detailed PiP image. This is test guidance data, not actual route guidance.

The detailed-model body matches ryseek's `phase_b_27` reference after changing only the inner/outer model IDs and high-guidance resource ID. Its 71-byte body is distinct from the existing V1 roundabout/road-icon model. V1 drawing code is unchanged.

## Offline validation

```sh
python3 -m unittest discover -s tests -p test_pip_trial.py -v
sh environment/build-pip-experiment.sh /private/captured/libscreen.so.1 /private/new-pip-build
python3 tools/audit_target.py /private/new-pip-build/supra-pip-window-marker-qnx \
  --runtime /private/captured-runtime --output /private/pip-arm-audit.json
python3 tools/prepare_pip_test.py \
  --binary /private/new-pip-build/supra-pip-window-marker-qnx \
  --audit /private/pip-arm-audit.json --create-response /private/create-response.bin \
  --capture-binary /private/new-pip-build/supra-pip-passive-capture-qnx \
  --capture-audit /private/pip-capture-audit.json \
  --v1-kit /private/current-v1-kit --output /private/new-pip-kit
```

Audit the companion passive-capture executable with the same audit command before packaging.

The build uses the existing private QNX SDK image, networking disabled, and the captured Screen library only as a linker input. It produces a separate executable; no V1 rebuild. Packaging rejects a stale/failed audit or a different V1 kit. The archive includes required third-party notices, not SDK or OEM libraries.

Nine tests cover actual loopback TCP framing, successful cleanup, occupied resource refusal, graph rejection, lost upload ACK/no reconnect, producer failure, forbidden factory-instance disposal and malformed profile rejection. These do not execute QNX Screen or emulate the cluster. Static target audit checks ARM32, interpreter presence, dependency closure and imported symbol names; not physical rendering.

## One coordinated session

The agent operates the tools; the owner only confirms readiness, observes the marker and performs the established iDrive restart. No broad discovery capture is required.

1. Park outdoors, engine running, ENET connected, V1 visible. Keep factory guidance/radio closed. Use the **existing accepted V2 validation kit** and `run_v2_validation.py` **preflight** and **pause-v1** phases from [V2-CAR-TEST.md](V2-CAR-TEST.md). Do not run its draw/boost phases. These phases verify the exact installed V1 files and stop it cooperatively without changing persistent tokens. Confirm both displays are clear.
2. Verify `/dev/screen/0/dpy-2` still reports OTHER2, 800×480, empty scene and no windows. Check the proposed private surface 9001 is absent through the existing LayerManager inspection command before creating it. If either output or surface is occupied, do not draw or remove it. The helper independently rechecks the stopped resident, absent broker/worker sockets and empty secondary output before creating its window.
3. Stage **only** the candidate in a new `/tmp/supra-pip-<unique-run>/` directory. Read back the executable and match the packaged SHA-256; make it executable. Run it with no arguments first: this prints usage and performs no Screen/network operations. Do not change filesystem protection or installed files.
4. Through the already-verified SSH master, establish a loopback-only forward to `160.48.199.96:30502`. Prepare two local JSON argv arrays: start runs the verified remote helper with `--parked-experiment 251658244 /tmp/supra-pip-<unique-run>/stop`; stop creates that exact private RAM stop file. Use `ssh -S <verified-master> -o BatchMode=yes` and the verified head-unit address. Quote remote paths; no factory paths belong in the stop command. Preserve both argv files in evidence.
5. Use a local asynchronous SSH process to run the packaged passive recorder in the foreground from the private RAM directory (do not wait on a remote background shell with a short command timeout). Start it using `--capture vlan73`, redirecting stdout to a PCAP and stderr to a separate log. This is the already-used non-promiscuous recorder: no transmitted packets, 120-second maximum, 64 MiB limit. Wait for its ready record before the drawing attempt. It records factory B009 sink changes alongside our B006 exchange so a failed marker does not require another discovery trip. Keep it running through cleanup, retrieve the PCAP and drop statistics before restarting iDrive. Then run the controller once, with a new evidence directory:

```sh
python3 tools/pip_trial.py \
  --create-response /private/pip-kit/create-response.bin \
  --support-profile /private/pip-kit/supra-profile.bin \
  --output /private/new-pip-live-evidence --execute \
  --v1-paused-and-displays-clear --guidance-stopped \
  --local-port VERIFIED_LOCAL_FORWARD_PORT \
  --producer-argv /private/start-producer.json \
  --producer-stop-argv /private/stop-producer.json
```

Before activation, the controller validates the helper’s `PIP_BINDING` record. The helper records active display state after first post and before removal. A mismatch prevents graph activation.

The agent announces the marker window as soon as the controller reports activation. Ask whether the border/cross appears in the **windshield**, **cluster**, or both, whether it is larger than V1, and whether the edges are clipped. Keep the engine idling. Do not start navigation or operate the radio during this brief experiment.

6. Read `result.json`: require native `local_cleanup=1`, every graph-withdrawal ACK, resource-dispose ACK and an absent post-dispose resource check. Re-read the secondary output and verify the private window/surface is gone. **Obtain separate visual confirmation that both displays are clear.** Neither an ACK nor a process exit is visual proof.
7. Owner performs the previously verified normal iDrive restart. Run the existing **verify-v1** phase with visible/updating V1 confirmation. Match the installed baseline files/configurations again. Cancel only this test's SSH forward. Keep logs and hashes before disconnecting.

## Failure and stop handling

An occupied resource causes no mutation. A rejected request triggers withdrawal/removal attempts. A broken transport is never reconnected for blind cleanup or replay; uncertainty remains recorded. Ctrl-C requests the helper's private stop file, waits for its report, then attempts graph withdrawal and resource removal. The helper has a local time limit; a hung Screen/IPC call or a lost SSH connection is **not** a guaranteed clean stop. An unconfirmed native stop or remote removal requires the established owner-operated iDrive restart and verification before V1 is considered recovered.

The tool never automatically resumes V1, deletes a quarantine marker, or disposes shared instance 200. Do not loop the test after an uncertain result. A cluster-only marker does not pass the windshield goal, and a blank output does not justify a speculative sink-switch command.

## QNX simulation

QNX 6.5 supports [VM targets](https://www.qnx.com/developers/docs/6.5.0SP1.update/com.qnx.doc.momentics_quickstart/about.html). The prepared SDK contains x86 Neutrino kernels and the older VMware graphics driver, but no x86 `libscreen`/Screen server at the checked target paths. [Screen 6.5 SP1 release notes](https://www.qnx.com/developers/articles/rel_6282_6.html) distinguish Screen from the older Photon graphics stack and list specific supported hardware. No compatible Screen VM has been established here. Even a generic Screen VM would not reproduce the Supra cluster's receiver or APIX/HUD routing. The shipped loopback tests are explicitly not a vehicle simulator.
