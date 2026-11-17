> Current next attempt: [factory-managed one-use boot trial](FACTORY-BOOT-TRIAL.md). Native drawing/cleanup passed; live PID replacement failed and is retired. The new boot gate is built and rehearsed offline, not yet accepted on the car. Unattended v1 remains unapproved.

Latest: [direct QNX runtime and pre-send navigation handoff candidate](STANDALONE-CANDIDATE.md); offline-tested, not yet installed or target-validated.

Latest: [sport UI live verified, orange/red corrected; v1 deployment boundary](SPORT-LIVE-RESULT.md).

Latest live result: [smooth RPM without circle or arrow, plus cooperative navigation yield](SYMBOL-FREE-LIVE-RESULT.md). Use the explicit empty-direction-zero profile; the old control is retained for comparison.

Latest prepared test: [explicit empty guiding model and cooperative navigation yield](SMOOTH-NAV-NEXT-TEST.md). The smooth live-RPM control is preserved.

Latest result: [smooth 30-second live RPM drawing verified](LIVE-RPM-SMOOTH-RESULT.md), with complete cleanup and normal factory-function checks. Circle removal and automatic coexistence remain unresolved.

Latest next test: [circle isolation, measured RPM input and factory-navigation handling](CIRCLE-RPM-NAV-NEXT-TEST.md). Includes review of the supplied windshield video.

Latest offline update: native tachometer frames and the bounded next drawing test are prepared. See [TACHOMETER-NEXT-TEST.md](TACHOMETER-NEXT-TEST.md) for validated scope, factory-navigation handoff and exact pass criteria.

> Latest offline status, 16 Nov 2026: do not repeat the capture sessions below. Engine-start, radio/navigation network recordings and three drawing-buffer states are saved. No live drawing test is ready. See [WINDSHIELD-RENDERER-TRACE.md](WINDSHIELD-RENDERER-TRACE.md) for the concrete test specification and unresolved entry criteria. Continue offline before requesting car time.

> On-car update, 16 Nov 2026: the loader, ten self-tests, replay and registry/overlay observations now pass. The expected 0x82/0 HUD service was absent in every window. See CAR-VALIDATION.md for measured results and cleanup. Earlier planned checks below are retained as procedure/history, not outstanding execution tasks. Live drawing remains blocked on actual Supra transport discovery.

# Next car session: exact test order

Vehicle: 2026 GR Supra 3.0 Premium, six-speed manual, NBTevo_T24081I. The first stage needs the car parked, ignition on and iDrive/HUD awake. Engine operation is unnecessary for loader/registry checks. The assistant performs the computer work; the driver only operates the factory menus when requested.

## What is already complete

The prior runtime captures are saved and static dependencies resolve. The SDK now builds three ARM candidates. Do not spend the next session repeating the entire library download or probing an automatic-transmission controller. No EGS exists for this manual-car project.

## First session priority: establish a working on-car test harness

| Order | Test | Evidence required before moving on |
| --- | --- | --- |
| 1 | Identify current wired interface, source address, gateway and direct OMAP address; verify known host key and `uname -a` | Direct `QNX hu-omap ... armle`, matching firmware/runtime identity; use current addresses, not historical ones |
| 2 | Check SSH and loader/library paths | Authenticated session; `/usr/lib/ldqnx.so.2` and candidate dependencies available. If SSH is closed, report it; activation is a separate access-state change |
| 3 | Check the temporary directory and copy the prepared kit there | New session-specific directory, exact local-vs-remote binary hash match (read back and hash on Mac if no target hash utility). This is a temporary file write, unlike earlier read-only capture |
| 4 | Run `sh run-selftest.sh`, recording stdout, stderr and process exit code separately on the Mac | Exit 0; schema 1; QNX target true; 32-bit pointers; all ten tests pass; vehicle_io false. Runtime is bounded by a five-second alarm |
| 5 | Optionally run `sh run-replay.sh` to compare emitted serialization | Exit 0; valid JSON; 40 synthetic calls; final function 0x20E. No messages are transmitted. This does not test HUD visibility |
| 6 | Run `sh run-observer.sh` for a 15-second normal-HUD baseline | Exit 0, complete schema-2 summary, temporary client connected, registry snapshots, zero HUD commands sent. Twenty-second hard deadline. Confirm a unique ring-node host of key 0x8200 if present |
| 7 | Repeat observer while opening/closing the radio selector; separately during a factory-navigation overlay if available while parked | Label each window and transitions; save snapshots and bounded header metadata. Header differences are clues, not validated overlay semantics. Missing traffic is not proof that no service exists |
| 8 | Check process exit, factory display and cleanup | No observer remains; factory HUD/navigation/radio still work. Retrieve all outputs, verify completeness, remove only this session's temporary files and directory after evidence is saved (the target lacks `rmdir`; verify the directory is empty before using `rm -r` on that exact session path), close SSH sessions, and record whether SSH remains enabled |

The kit contains three separate scripts. Running the self-test never starts the observer. The observer creates temporary DSI client registration/subscriptions but does not register device-control keys, allocate HUD objects, send drawing messages or change coding/firmware. Its private ABI is partly derived from captured binaries; its first execution remains an experiment, not a previously verified runtime.

If the loader/self-test fails, stop before the observer. Save the exact loader error/exit status and inspect only the newly implicated files. If the observer crashes, times out, loses the link, sends any HUD command, drops data, or returns ambiguous registry hosts, retain the evidence and stop escalating. Do not substitute the original hardcoded worker or guess a drawing handle.

## Local output validation before unplugging

```sh
python3 tools/check_session_result.py selftest.log --kind selftest \
  --exit-code 0 --output selftest-check.json
python3 tools/check_session_result.py registry-baseline.log --kind registry \
  --exit-code 0 --output registry-check.json
```

Pass the actual captured exit code, not an assumed zero. The checker rejects incomplete JSON, wrong architecture, missing/failed self-tests, nonzero process status, nonzero transmissions, truncated captures and absent/ambiguous HUD hosts. An evidence pass does not authorize drawing. Save separate radio/navigation results even if the registry test passes but no relevant headers appear.

## Still required before live tachometer drawing

1. **Object ownership and transport:** prove the actual Supra HUD service, safe creation/acquisition of two exclusively owned objects, and the release contract. A registry entry alone does not give ownership; fixture handles 20/21 must never be copied into a live profile.
2. **Acknowledgements:** verify source/destination, operation, echoed tag and payload behavior on this firmware. The current exact-echo contract is deliberately unverified and disabled by default. Header-only captures cannot prove payload echo.
3. **Geometry and palette:** measure native windshield coordinate bounds, position, clipping, line width, item capacity and color indexes using only verified owned objects. Center-screen 1280x480 evidence is not windshield geometry.
4. **Timing and freshness:** measure acknowledgement latency and a workable update strategy. Forty calls spaced 50 ms apart take at least 1.95 s; the production 300 ms sample-expiry gate now rejects that stale frame. Do not solve this by silently raising the production TTL. Optimize verified transport/geometry updates and demonstrate the needed cadence first.
5. **Factory overlays and recovery:** verify radio/navigation priority, visible yield, return, stale-input behavior, disconnect, timeout and process-exit cleanup. Stopping local sends does not prove an already visible remote object disappears. No persistent startup until lifetime/cleanup is proven.
6. **Telemetry and calibration:** compare live RPM against the factory reading with the engine running normally while parked. Confirm a user-approved shift target and redline for this actual car/configuration; 7000/6500 in fixtures are examples. Boost stays hidden until source, units and ambient reference are validated across appropriate conditions; idle pressure alone is insufficient. Gear/oil temperature remain optional and unimplemented.

No live drawing sender or production profile is currently enabled, so the immediate session is for execution/discovery/overlay evidence. A successful session does not promise finished visual drawing that day. Before unplugging, explicitly mark every planned item complete, failed or deferred in RESULTS.json and save the package to Drive.
