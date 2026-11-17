# Persistent tachometer install candidate — 16 November 2026

See [17 November live validation](PERSISTENT-LIVE-VALIDATION.md) for target-specific corrections and current evidence.

The application now has a resident supervisor, continuous live RPM, automatic navigation/radio handoff and return, two factory-managed startup gates, a persistent enable token, and exact-image rollback. This is the install path; it has no 30-second run limit. It is built and tested offline, **not installed or accepted on the Supra yet**.

## Why the last run could not stay installed

The last continuous run displayed 432 smooth frames over about 108 seconds. Opening the radio selector reached the worker through passive observation, after factory drawing had already started. The worker stopped but could not safely erase shared factory state; both test bitmap resources remained until a normal iDrive restart. The final restart removed them, restored original startup, and the user confirmed factory functions were normal.

The navigation pre-send handoff already worked on the car. Radio uses a different C++ calling interface in HmiMain3D. The new hook covers both interfaces and waits for verified tachometer removal **before** allowing either factory writer to continue.

## Automatic return

The supervisor starts before the hooked factory processes. It correlates pre-send events, actual Ethernet requests and successful replies. Guidance is idle only after its known main visibility model is committed. Radio is idle only after the captured list-control clear-focus value `0xffffffff` is committed. Both lanes must be explicitly idle; boot state is unknown. Child-model/resource updates do not invent a new visibility state, but every outstanding request blocks admission.

The worker removes its model references and both alternating bitmap resources before acknowledging a handoff. The supervisor remains running while navigation or radio owns the display. After both acknowledged idle states, it launches another continuous worker. A 200 ms coalescing delay reduces churn after message bursts; silence alone never authorizes drawing.

Missing drawing acknowledgements, uncovered writers, capture loss or uncertain removal disable automatic retries. Verified-clean RPM transport failures use bounded 1/2/4-second retries, with at most three consecutive unstable attempts. A heartbeat makes the worker stop if its supervisor disappears. Logs are bounded. Neither hook disposes the shared factory session.

## Offline evidence

- Real host supervisor and worker against loopback protocol peers: initial standby, navigation cleanup/return, radio cleanup/return, three worker starts, final clean stop.
- Lost-acknowledgement case: quarantine and persistent disable, no blind restart.
- Lease/stream tests: stale acknowledgements, resource/child-model updates, fragmented messages, retransmissions, gaps, uncovered writers, repeated worker connection turnover.
- Both factory calling interfaces: legacy handoff cases plus persistent broker framing.
- Startup fixtures: original same-PID exec, one-use trial shared by both gates, persistent enable, disabled fallback.
- Transaction fixture: second-file failure followed by exact restoration of both original configurations and read-only protection.
- QNX ARM build and static runtime import checks are separate from actual target execution.

## Prepared installation workflow

Use `tools/prepare_persistent.py` to make the private kit from the captured original configurations, verified profile, factory executables and current build. The kit contains hashes, original and replacement configurations, eight native components and the profile. Proprietary captures and compiled artifacts stay out of GitHub.

`tools/persistent_install.py` defaults to a no-action plan. Execution requires the private kit, a new local evidence directory and an already verified SSH master socket. Use the same values for all phases:

```
python3 tools/persistent_install.py PHASE --execute --kit KIT --output EVIDENCE --ssh-socket SOCKET
```

1. **preflight**: compare both factory executables and original startup files; ensure neither hook is loaded; inspect the actual HMI SomeIP library exports before any write. This library was not captured previously. If it differs or is absent, stop before changing startup.
2. **install**: stage and read back every byte, install both same-PID gates, change only the two exact process names, restore read-only protection. This is unarmed; a normal restart must return factory HUD/iDrive without drawing.
3. **arm**: consume a one-boot trial token on the next normal volume-knob restart. Both gates share this boot; the real continuous resident runs. There is no short demo timer.
4. **collect**: save status, worker results and bounded journals at each checkpoint.
5. **commit**: after the acceptance sequence below, enable the same resident on subsequent boots. It keeps the current accepted run running; it does not stop it or restore factory startup.

The commit command additionally requires `--startup-confirmed --navigation-return-confirmed --radio-return-confirmed --cleanup-confirmed`. These flags record actual observations, not substitutes for testing. It also checks mapped hooks in both factory processes, unchanged installed bytes, advancing heartbeat, at least three worker starts and two clean stops, acknowledged active/idle transitions for both lanes, at least five minutes of supervisor uptime and at least 1200 frames in the final uninterrupted worker run.

## Exact acceptance sequence in the car

Keep the car parked outdoors. Establish normal factory operation, then perform the unarmed and armed normal restarts above.

1. After the armed restart, confirm the tachometer starts automatically, reads live idle RPM smoothly, and shows no circle/arrow. If the firmware has not established both idle states, the app must remain in standby. Do not fake a boot-idle default or commit a manually coaxed startup as automatic startup.
2. Start factory guidance while the tachometer is visible. Confirm the tach disappears and navigation works in both displays. Stop guidance; confirm the tach returns by itself. Check the logged clean handoff and committed release.
3. Open the radio selector while the tach is visible. Confirm removal before the selector displays normally. Let it close; confirm the tach returns by itself. Repeat radio open/close to exercise transient focus changes. Check no retained custom resources at each stopped handoff.
4. Leave the final resumed worker running for at least five uninterrupted minutes and 1200 logged frames. Confirm smooth live RPM and normal iDrive; collect evidence. No fabricated high-RPM engine test is required.
5. Commit persistence only after all checks pass. Perform a final normal restart to verify committed automatic startup and one radio return, then leave the app running. Save evidence before unplugging. A cold sleep/wake check remains a separate follow-up if time does not permit a full sleep cycle; do not report it as tested.

## Disable and rollback

`disable` requests cooperative verified removal and writes the persistent disable flag. `rollback` stops the resident when present, disables future activation, restores both exact original configuration images using inode-preserving helpers, and restores read-only protection. It does not claim that restoring files unloads already mapped hooks. A normal volume-knob restart is required, followed by `verify-restored --factory-normal` after visually checking factory functions.

If installation fails partway, retain the evidence directory and use `rollback`; never rerun staging blindly or overwrite an unexpected configuration. If cleanup cannot be verified, do not claim removal: use the already verified normal restart recovery, then inspect and restore. A consumed trial cannot silently rearm on the next boot.

## Remaining target-specific checks

The HMI library exports, HMI startup gate, real radio handoff/return, initial boot visibility events, continuous capture across boot, and committed restart behavior require the prepared acceptance above. Offline tests establish implementation behavior under the exercised fixtures; they do not prove these firmware-specific interactions. The persistent candidate remains parked-validation software until those checks pass.
