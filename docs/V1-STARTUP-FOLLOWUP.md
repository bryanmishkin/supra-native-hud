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
