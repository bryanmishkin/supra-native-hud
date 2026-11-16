# Consolidated evidence runner and startup strategy

16 November 2026. Offline engineering complete for this runner revision; no vehicle deployment performed. The runner is tested and built. Full cold-boot capture and arbitrary surface allocation are NOT proven.

## New static answers
- `0xab3788` handles `MyRicConnectionNotification`. A false connected byte clears handle +0x1c and state +0x8c. A true connected byte calls dispatcher `0xab3670` at `0xab37d8`, then sets +0x8c. This is a concrete creation trigger tied to service connection, not every route-guidance start.
- Dispatcher `0xab3670` selects IC request `0xab3408` for selector 0 and HMI request `0xab353c` for selector 1. The IC request constructs `BMW.IC.Guidance`, `ICGuidanceControl`, `BMW` and a version-like constructor with arguments 3,3,1. The HMI alternative constructs `BMW.HMI.Roadbook`, `RICController`, `Harman` with the same numeric arguments. These are observed argument values, not a recommended identity to impersonate.
- Result handler `0xab3108` stores the first returned word at +0x1c, logged as mHandle at `0xab314c`. This establishes a factory service-object lifecycle. It does not show that a newly named application can obtain arbitrary pixels, a private windshield region or compositor priority.
- Error handler `0xab3688` retries creation on error code 4 only when +0x8c is true. Do not deliberately generate an error to trigger it.
- DisplaySink consumer `0xa7a200` logs the first field as `displayAspectRatio: %f`, the fixed u16 array as resolution, and the trailing byte as display selection. This advances the previous raw-only field interpretation: the saved event carries aspect ratio 1.0 and resolution pair 460/237. Axis order is not independently proven. Do not label this as the physical windshield's full resolution.
- The selection branch `0xa7a51c` sends incoming zero to the branch logged “Kombi switch to Hud,” while nonzero reaches “Hud switch to Kombi.” This is NOT evidence that captured selection 1 means HUD. Internal state flags and external selection must remain distinct. Displayable-session checks still gate routing.

## What startup capture can and cannot do
A recorder started via SSH cannot observe a factory create exchange already sent before SSH was available. A full HU reboot kills this recorder and may disable temporary SSH. The OBD-side Ethernet link has not been shown to mirror internal vlan73 traffic. Therefore neither “start navigation again,” “reboot while streaming,” nor “record on the Mac instead” is an established cold-boot solution.

The least intrusive candidate is **retained-HU connection capture**: keep the head unit/SSH alive, arm the internal recorder, then observe a user-controlled ignition/cluster wake transition. This can capture creation only if the relevant cluster service reconnects while recording survives. That physical behavior has not been verified. No automatic ignition change, service restart, injected create request, startup script or persistent installation is in this runner.

For the next parked session, establish access with iDrive awake before the intended ignition transition if possible. Collect the broad evidence bundle, then start the continuous recorder. Wait for its actual `recording_ready` output before an operator asks the user to change ignition state. Record markers at the observed actions. Do not start the engine or move the vehicle. If access dies, preserve the partial capture and report the gap; do not claim a successful startup recording or improvise a reboot loop. If connection is already established and no reconnect occurs, the result is “creation not observed,” even if navigation appears.

A guaranteed full cold-boot recording would require a separately designed boot-persistent recorder or a verified internal-network tap/mirror. Neither is implemented or authorized by the read-only capture workflow. That limitation is explicit rather than a promise of another “final” trip. Broad static evidence collection remains valuable even if retained-HU creation is not observed.

## One consolidated collection
Use the existing isolated Python environment with requirements-static.txt. Tool defaults print a plan and make no connection:

```sh
python tools/consolidated_capture.py
```

With the current verified wired addresses, dedicated known-hosts file and an already authenticated SSH master:

```sh
python tools/consolidated_capture.py --execute \
  --head HEAD_IP --local MAC_ENET_IP --known-hosts KNOWN_HOSTS \
  --socket SSH_SOCKET --output PRIVATE_SESSION_DIRECTORY
```

The literal placeholders must be replaced from that session's preflight, not reused stale addresses. No password or SSH activation is built in.

The collection includes NavNBTEvoController, NavigationBasic, NavigationFully, NavigationOnOff, the SOME/IP daemon/server, known configuration files, extra navigation configuration paths from current process arguments, per-navigation-process memory maps, current sockets/interfaces/loader path, mapped library candidates and recursive DT_NEEDED dependencies from fixed library directories. It reports inaccessible/truncated-name candidates instead of silently claiming coverage. Library-directory ordering alone cannot prove which duplicate runtime library is loaded; the maps remain required evidence. It does not claim that memory maps alone identify the DSI service provider.

Every new file is read twice and must match. Resume verifies the saved local SHA256 and performs a fresh remote read before reusing a file. Changed or corrupt cache entries require a new matching pair. This deliberately spends one read on resumed files to avoid assuming firmware/runtime stayed identical. Manifest writes are atomic and per-file failures persist. Missing NavCtrl_DB.ini is an explicit optional-override result, not a successfully captured file.

Limits: 64 MiB/file, 512 MiB/session received data, 20-minute collection budget, 45 seconds/read, 128 DT_NEEDED names, at least 1 GiB free local disk. No firmware/coding changes, remote configuration writes or service restarts. Phase duration depends on actual transfer throughput; the six primary executable files are roughly 46 MiB based on captured listings, before libraries/configuration and duplicate verification reads. Do not promise a fixed session length from Ethernet link speed alone.

## Continuous transition recording
The QNX build now produces `build/supra-continuous-capture-qnx`. Use the exact SHA256 from the private recorder static-gate report for this build:

```sh
python tools/consolidated_capture.py --execute --record-only \
  --head HEAD_IP --local MAC_ENET_IP --known-hosts KNOWN_HOSTS \
  --socket SSH_SOCKET --output PRIVATE_SESSION_DIRECTORY \
  --binary build/supra-continuous-capture-qnx --sha256 VERIFIED_BUILD_SHA256
```

`--record` after a collection runs both phases sequentially. `--record-only` avoids repeating file collection. Each recording gets a new local folder.

The runner verifies direct ARM QNX identity and UP vlan73 at 160.48.199.119; uploads only the exact ARM recorder into a unique /fs/ram5 directory; reads it back; streams PCAP directly to the Mac; checks process absence and deletes its own temporary files. Cleanup bypasses the collection budget so budget exhaustion does not prevent cleanup attempts. Failed cleanup is a separate failed gate. The runner does not close a user-provided SSH master or disable the SSH server.

Recorder: 120 seconds, 64 MiB, 65,536 packets, 130-second independent alarm, non-promiscuous. It captures all TCP/UDP ports involving observed cluster peers 160.48.199.96/.97, plus UDP port 30490 discovery. New peer addresses must be checked in preflight; this is not a claim to record every device on the VLAN. Discovery payloads are retained in raw PCAP; the current parser counts UDP but does not decode SD semantics.

An operator can mark observed actions in the active recording folder:

```sh
python tools/capture_mark.py RECORDING_FOLDER ignition-off
python tools/capture_mark.py RECORDING_FOLDER ignition-on
```

Other supported markers: baseline, radio-open, radio-close, guidance-start, guidance-stop, factory-normal. Markers are host-clock observations, not vehicle acknowledgements. A remote date sample brackets the clock offset with one-second remote resolution and network delay; packet timestamps and host markers must not be assumed perfectly synchronized.

## Automatic evidence gates
- Each verified file: length/hash and matching reads; local hashes checked again at end.
- PCAP: exact packet lengths, no IP fragmentation, TCP continuity/conflicting-overlap checks, byte/packet bounds, zero reported capture drops, full duration and matching PCAP byte count.
- Timestamp provenance: per-stream byte spans preserve original packet numbers and microsecond timestamps, including reordering/retransmission. Message bounds include all overlapping packets; they are not exact application event timestamps.
- Every parsed B006/B009/B00E message is cataloged with connection, method, request/session, body hash/length and timestamp bounds.
- A B006 method-1 request must have one unambiguous successful matching reply on the same connection and interface before `creation_exchange_observed` becomes true. That is protocol acceptance only. It does not set startup completeness, prove initialization/disposal, or grant ownership.
- Missing/ambiguous/unparsed data and cleanup failures remain visible. `provider_binding_proven`, `independent_surface_proven` and `startup_covered` remain false until separately established.
- Before releasing the user: review manifest/result/lifecycle reports, confirm factory behavior, verify local evidence, and state which questions remain unresolved. A green file pass must never be summarized as “we have everything for the project.”

## Validation
72 host/Python tests passed, covering resumable reads/corrupt cache, changing or missing files, wrong host, budget-safe cleanup, malformed capture, bad upload, live-process cleanup failure, recorder hard bounds/errors, exact protocol envelopes, timestamp preservation and false startup/ownership claims. All five saved captures (1,093 packets; 90 TCP directions) parse under the new extractor; none contains the matched guidance create exchange. The QNX ARM build and captured-runtime static import/dependency gate pass. No new binary has been run on the car.
