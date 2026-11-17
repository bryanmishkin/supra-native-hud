# Startup follow-up — 17 November 2026

The earlier accepted shutdown/start record is one successful cycle, not proof of reliable cold startup. A subsequent boot initially showed no tachometer and later recovered. Its saved Ethernet capture contains eight TCP SYN requests to internal gateway 160.48.199.16:6801 answered by RST/ACK before a successful connection and RPM replies. The first saved successful run begins around 193 seconds of head-unit monotonic time. PCAP wall time changes during clock synchronization; do not subtract its first packet timestamp across that jump.

A further controlled startup remained blank after five minutes cable-free, car-end-only ENET insertion, and laptop connection. Retrieval found a different definitive blocker: persistent `disabled` = `worker startup deadline`, terminal record `QUARANTINED: worker startup deadline` with `cleanup_proven=true`, and both gates reporting `persistent-disable-present`. All 15 installed payload/config comparisons matched the accepted repair. This trial cannot determine cable dependence because the app was disabled throughout it.

## Reproduced defect and correction

The resident checked for a missing worker control socket more than three seconds after fork even after admission. A running worker can remove that socket during clean RPM-failure teardown before the parent observes process exit. The old code then falsely quarantines and persists the startup deadline, blocking the next boot.

The startup watchdog now applies only before admission. Reaping and verified result/cleanup continue to govern admitted workers. Uncertain cleanup still quarantines; this is not a general clearing of disable tokens.

`tests/resident_startup_deadline.py` reproduces the exact quarantine with old source after a healthy >3-second run, clean input failure and a delayed exit. Corrected source recovers cleanly; a child that genuinely never starts still triggers the deadline.

Deployment requires exact installed hashes, stopped app, the exact saved fault plus cleanup proof, and two read-only empty-resource checks. Only the supervisor changes. Preserve the fault token in an archive after validated replacement, keep enable/startup/worker/profile unchanged, and restore read-only protection.

Installed on the reference car after exact 15-file baseline comparison and two empty-pool checks. Only resident changed: SHA-256 `d49da8e89dc03e695283fb86297e9fc1d77b0811e6fba3720e13a7bda51d1d9b`. Fault token archived, persistence preserved, read-only mount restored. Targeted before/after reproduction, 251 Python tests, resident recovery regressions and ARM static audit passed. Normal shutdown/start validation is pending. Earlier gateway rejection/delay remains a separate question; do not claim this watchdog correction proves cable-free gateway readiness.

## Remaining gateway dependency and factory RPM replacement

A subsequent ten-minute, fully cable-free shutdown/start still produced no tachometer. It appeared after ENET reconnection, before SSH activation. That boot had no disable token or quarantine: the repaired resident kept retrying. Seven internal gateway SYN attempts were answered by RST/ACK; the first accepted connection followed 130.526 seconds after the first saved attempt. This proves RPM transport unavailability, but timing alone does not prove the cable caused availability.

Offline HMI tracing identified `CPxyVehicle::CEngineSpeed2`, function `0x0cd0` in Vehicle FBlock `05/00`. A fresh MOST registry resolves that block to local provider `0x5000`. A bounded read-only DSI client received Status (`0xC`) messages containing two big-endian bytes in quarter-RPM units. During a two-minute recording including owner-confirmed ENET disconnection, 1,196 samples arrived with a maximum gap of 145 ms. Against 430 overlapping diagnostic RPM samples, mean absolute difference was 1.394 RPM, maximum 9 RPM. This establishes a working idle engine-speed feed without diagnostic TCP port 6801. Scale outside the observed idle range is inferred from the same encoding; high-RPM live calibration is not claimed.

The new worker uses this factory feed for drawing. It subscribes only to Vehicle 05/00, issues one read-only EngineSpeed2 GET after the expected registry/registration are present, and accepts only correctly addressed, normal-class, two-byte Status replies in range 0..7700 RPM. It does not send SET/control/ECU commands. Samples must advance and be no older than 200 ms on acquisition; existing 300 ms render freshness and factory admission/cleanup remain. Missing/stale input exits through verified cleanup and the existing rate-limited supervisor recovery. Explicit `--probe-rpm` remains a diagnostic research command; the native drawing path does not invoke it.

### Temporary probe crash and exit correction

An early read-only worker probe received 100 samples but crashed while exiting, in `libstdc++.so.6` (`__exchange_and_add`). iDrive then restarted; the saved core and reboot evidence are preserved privately. Treat the probe as the suspected trigger, not a successful stability result. The DSI library owns background threads without a supported join API. Corrected worker execution completes HUD cleanup and local object destruction, flushes its result, then uses `_exit` on QNX to avoid concurrent process-wide C++ teardown. The earlier bounded observer already used this exit approach. The corrected on-unit probe exited 0, and the installed worker subsequently completed a factory-request cleanup and returned without a process fault.

QNX library resolution also needs `LD_LIBRARY_PATH=/opt/sys/lib:/boot/lib:/lib` at launch. The worker re-execs itself once with that exact path before threads, sockets, admission or drawing. This was tested with the SSH-inherited path explicitly unset. It changes only the worker environment.

### Exact installed candidate — cold-start acceptance pending

Only the worker was replaced; resident, hooks, startup configuration, enable token, V1 artwork and profile remain unchanged. Installed worker SHA-256:

`591e50f74d9e88390f61e402f8bc658d2f318b80e008ccb75082e50419b7a35f`

The previous worker is preserved on the reference head unit as `supra-standalone-parked-qnx.before-factory-rpm-1007744e`. The private install receipt contains the complete path and all readbacks. All 15 baseline comparisons matched before replacement and all 15 revised-reference comparisons matched afterward. Filesystem protection is restored. Cooperative replacement returned CLEAN. The owner confirmed the new tach was visible and smoothly updating. The supervisor remained healthy and the frame counter advanced.

Host tests cover decoding/address/operation/length/sentinel checks and native-feed drawing with zero diagnostic requests, stale-feed cleanup, and unavailable-feed rejection before any image upload. ARM dependency/import audit and the corrected on-unit read-only probe passed. **A fully cable-free ten-minute shutdown/start is now being tested; do not claim it passed until the owner confirms it.**

Private evidence is in the 17 November repeat-cold-failure package, `ten-minute-boot/` and `factory-rpm-fix/`. Do not upload factory binaries, core dumps or private profiles to GitHub.


### Build and result-reading notes

`environment/run-local-sdk-build.sh` builds the native-feed worker via `build-observer.sh` with `SUPRA_FACTORY_RPM`, `src/factory_rpm.cpp`, and the preserved vendor DSI client. Host builds without that macro retain the diagnostic simulator for the existing protocol regression suite. `tests/factory_rpm_integration.py` separately tests the native-feed branch with a controlled source and asserts zero diagnostic requests.

`--probe-factory-rpm` is a bounded, no-drawing native-feed check (100 advancing samples). `tools/engine_speed_probe.cpp` is a separate two-minute discovery recorder, with at most 12 read-only GETs; it requires `--read-engine-speed`. Do not substitute either for actual unplugged cold-start acceptance.

The vendor DSI client emits a startup text preamble on stdout. For this candidate, `worker.result`/`last-result` contain that preamble followed by the terminal JSON result; the unchanged resident already checks the required terminal fields without assuming a single JSON-only file. `run_v1_validation.py` now accepts only that known preamble followed by a structurally valid terminal JSON result; missing results, unknown preambles and trailing junk are rejected. Other external consumers must likewise read the terminal result rather than assume the whole file is JSON.


### First normal start after factory-feed replacement

The owner confirmed engine off, ENET fully removed, doors locked and key away at 20:30:20 UTC. The owner chose to start before the planned ten-minute deadline; record this as approximately eight to nine minutes, not a verified ten-minute soak or overnight cold boot. At 20:39:36 UTC the owner reported automatic tachometer appearance with ENET still unplugged. The precise engine-start timestamp was not captured, so no exact startup latency is claimed. Sustained updating confirmation is pending. This is evidence for this revised input path on the reference car, not a universal/repeated-start guarantee.


## Sustained movement failure — acceptance withdrawn

The owner subsequently drove briefly: the tach disappeared, returned, then disappeared after reversing and pulling forward. The earlier automatic-appearance observation is **not** sustained-operation acceptance. The first native-feed worker logged `rpm_transport:factory feed stale`; it had requested once and incorrectly relied on continued spontaneous delivery. The next worker requests EngineSpeed2 at most every 100 ms from a serialized sender, following the verified cross-thread send-lock pattern in `vendor/nbt/src/most/client.cpp`. The drawing loop never blocks on that sender. The movement reproduction on that version had zero input retries, but still stopped for factory traffic.

The exact second failure was captured:

- Request: `b0060008000000100001002001010000000000c803000004`
- Reply: `b0060008000000080001002001018101`
- This is factory service `0xb006`, remove-resource method 8, handle 200, text resource `0x03000004`, with error type `0x81` / return code `0x01`.
- Runtime: clean tach withdrawal, then persistent `factory request failed` quarantine. All ten bitmap slots were independently empty; filesystem read-only. This was not a failed removal of either custom bitmap (`0x01000008/09`).

The capture also contains repeated RoadInfo model `0x11000000` / type 17 updates while factory guidance and radio remain idle. Treating every such request as a takeover repeatedly removed the tach while moving. The old parked tests did not expose that path; the Gold Master road-readiness claim was premature.

### Movement correction

The supervisor now distinguishes the measured background RoadInfo model, factory text namespace `0x03xxxxxx`, and an idle-only commit from guidance visibility, maneuver/road-image bindings, sessions and custom bitmap operations. Background pending requests do not revoke admission or restart the quiet-period clock. Actual navigation/radio visibility changes still revoke admission.

Before forwarding any background request while the worker is drawing, the supervisor sends the exact normalized message over the private control socket and requires `READY`. The worker's passive monitor accepts only those authorized bytes, with bounded TCP reassembly, exact retransmission checks, gap rejection and cookie tracking. It does not simply ignore a port, assume every partial packet is safe, or infer permission from a plausible embedded header. Failed authorization falls back to normal cleanup. Unknown messages and traffic still withdraw conservatively.

The one captured negative text-deletion reply is retained as evidence and counted without inventing successful deletion or changing visibility. It cannot establish idle. Errors involving bitmap/model/session operations still fault; the app never deletes factory text resources to suppress the error.

Offline replay through the real supervisor and worker processed 94 captured background requests and the exact negative text-removal reply with one continuous worker and no clear/restart. A real visibility takeover still cleaned up and returned; changing the rejected resource into the bitmap namespace still quarantined. Fragmented, coalesced, repeated, conflicting, unauthorized and mixed traffic tests passed. Existing 12 worker cases and 253 Python tests passed; the full QNX build and ARM import/dependency audits passed.

Installed candidate (owner-observed connected drive passed; cable-free startup/drive pending):

- Worker `91191ffed2d15f566bafcf916054cff0c0910c74c88f69c4337b6a87dafe3217`
- Resident `42071e048e9b32434fd52e3fe9f5496a2baa4daae2b6ab7778a89f8d5bd601fa`

All original hooks, gates, V1 layout/profile and enable state remain. The private install receipt verifies the exact prior 15-file baseline, two empty-pool checks, replacement readbacks, archived fault token, rollback binaries and read-only restoration. The owner returned for a targeted movement check; no additional mock classes are being implemented during that car session.


### Connected movement result and next acceptance check

After restarting iDrive on the movement correction above, the owner confirmed the tach was visible, then reported: “Ok I drove around it held”. This is an owner-observed successful connected drive. Duration and route were not recorded; post-drive worker continuity and frame counters have not been independently retrieved. Do not describe it as an endurance result or a cable-free cold-start pass.

The owner then confirmed engine off, ENET completely unplugged from the car, doors locked and key away. The shutdown timer began at 15:20:38 America/Chicago on 17 November 2026 (21:20:38 UTC); the planned ten-minute interval ends at 15:30:38. The remaining test is a normal start without the laptop, automatic advancing tach display, followed by driving without dropouts. Result pending. The elapsed interval alone does not prove full vehicle sleep.

The original Gold Master tag remains unchanged. Startup configuration and enable state were preserved by this movement correction; persistence is expected, but acceptance requires the pending unplugged start/drive result. No unrelated radio/navigation retests are requested.


## Accepted cable-free startup and drive — 17 November 2026

The owner reported: “Tach came on with the cable unplugged and stayed on during the drive. I'm parked now.” This completes the requested owner-observed normal shutdown/start and driving check on the exact movement-correction binaries listed above. The car had been shut down, locked with key away and ENET completely removed. The owner elected to return before the planned ten-minute deadline; the precise shutdown duration, start latency, route and drive duration were not measured. Do not claim a ten-minute soak, verified full ECU sleep, overnight cold soak, repeated-cycle or extended endurance validation.

Evidence is deliberately separated: installation receipts establish exact binary readbacks and restored read-only protection; the owner establishes automatic cable-free appearance and sustained visibility during this drive. No post-drive machine logs were retrieved for this result. No new changes to the car were made when recording acceptance.

Accepted application source is commit `74dd185`; subsequent commits update documentation only. Worker SHA-256 `91191ffed2d15f566bafcf916054cff0c0910c74c88f69c4337b6a87dafe3217`; resident SHA-256 `42071e048e9b32434fd52e3fe9f5496a2baa4daae2b6ab7778a89f8d5bd601fa`. The private archive preserves the exact installed kit, manifest, rollback configurations, install receipts, source snapshot and offline test reports. The historical `v1.0.0-gold-master` tag is unchanged; this accepted repair supersedes its runtime for the reference vehicle.
