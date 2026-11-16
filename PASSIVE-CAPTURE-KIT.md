# Next-session passive capture kit

Built and tested offline on 16 November 2026. **Not yet tested against this car's BPF device.** No car connection was made during preparation. The private ZIP contains the ARM executable; GitHub contains source only.

## What is ready
- QNX 6.5 ARMv7 recorder, 153,569 bytes. Static dependency/import audit passes against the captured `libsocket.so.3` and `libc.so.3`. libpcap is linked from the local SDK. No SDK, license material or OEM binaries are published to GitHub.
- Non-promiscuous capture on one explicitly selected interface. Filter: hosts 160.48.199.96 or .97, TCP/UDP ports 30501–30503, both directions. This deliberately targets the known candidate channels; a negative result does not exclude other ports or peers.
- 15-second window, 8 MiB output maximum, 4096 packets maximum, 65535-byte snapshot, 20-second process alarm. Capture goes straight to the Mac over SSH, not to vehicle storage. Failed setup, drops or early limits are not a complete capture.
- Host runner verifies the interface's active internal IPv4 address, verifies the candidate hash, creates a unique RAM directory, uploads and reads back the candidate, captures, and removes its own RAM directory. No activation/unlocking, passwords, network setting changes, reboot or persistent installation. Existing verified SSH access is required.
- Offline classic-PCAP extraction checks packet completeness and TCP continuity, handles sequence wrap, ordering and identical retransmissions, and rejects gaps/conflicting overlaps/fragmented IPv4. UDP packets remain in the original PCAP. Unsupported link types or formats fail explicitly.
- A stream beginning mid-message is preserved, not guessed. Even syntactically valid SOME/IP headers do not prove a boundary, display target or ownership. No live drawing permission is granted.

## Exact run order (Mac, from extracted kit directory)

1. Park, ignition on, iDrive awake. Establish previously reviewed temporary SSH if needed. The runner never activates it. Use the current verified address; these commands use the previously verified OMAP address.
2. Run read-only preflight first:

```sh
python3 run_passive_capture.py --host root@169.254.199.119 --output preflight --preflight-only --execute
```

Review `preflight/preflight.txt`: QNX/OMAP identity, `/fs/ram5` RAM mount, internal VLAN and address, BPF devices, and interface status. Current expected logical interface is vlan73 with 160.48.199.119. Do not switch to the physical interface, enable promiscuous mode, load drivers or alter routing if capture fails. Interface enumeration alone does not prove BPF access. Missing BPF support is an explicit remaining car-side blocker.

3. Let radio/navigation overlays settle to normal. Then run:

```sh
python3 run_passive_capture.py --host root@169.254.199.119 --interface vlan73 --label baseline --output baseline --execute
```

The command without `--execute` is a dry run. Existing output directories are rejected to avoid overwriting evidence. For radio, keep the selector visible as possible and record Mode presses; for navigation, show a stationary factory instruction. Run each separately after confirming its visible state:

```sh
python3 run_passive_capture.py --host root@169.254.199.119 --interface vlan73 --label radio --output radio --execute
python3 run_passive_capture.py --host root@169.254.199.119 --interface vlan73 --label navigation --output navigation --execute
```

4. Check each `result.json`: actual exit code 0, `capture_valid: true`, no drops, duration at least 14.5 seconds, nonempty packets, and `cleanup_verified: true`. This means capture completed, not HUD protocol proven. `inventory.json` may report a stream parse error if capture began mid-message. Preserve raw PCAP regardless. Confirm factory HUD/radio/navigation still work normally.
5. Extract streams locally for deeper review:

```sh
python3 extract_someip_pcap.py baseline/baseline.pcap baseline-streams
python3 extract_someip_pcap.py radio/radio.pcap radio-streams
python3 extract_someip_pcap.py navigation/navigation.pcap navigation-streams
```

Do not unplug until raw files, hashes, summaries, cleanup results and visual observations have been checked locally. Save all three private windows to Drive. Route names and other vehicle data may be in the payloads; raw captures do not go to GitHub.

## Still needed on the car
BPF availability, actual capture visibility in both directions, active cluster selector/display destination, service/method identities, independent object ownership, overlay arbitration and latency. A capture failure is not authorization to inject traffic or alter configuration. No draw/erase test is ready yet.

## Offline test coverage
30 Python/host tests pass, including deterministic capture fixtures for empty windows, packets, size limit, drops, read/write errors, unsupported link/filter setup, and no default capture; PCAP reordering/retransmission/wrap/truncation/gap cases; host dry-run, input validation, upload/readback and cleanup. These mocks do not substitute for QNX BPF validation. ARM compilation and static target audit pass. Existing HUD core binaries remain separate from this recorder.
