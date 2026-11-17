> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# On-car validation — 16 November 2026

Vehicle: 2026 GR Supra manual, NBTevo_T24081I; direct QNX 6.5 ARM OMAP. The source repository contains this summary, not raw vehicle captures or OEM binaries. Complete private evidence is in the Drive diagnostics bundle.

## Results

- All 12 libraries in the candidates' linked/DSI dependency closure matched the saved runtime hashes.
- All uploaded executable bytes matched local read-back hashes.
- Ten self-tests passed on the actual QNX 32-bit target; synthetic replay returned 40 commands with visibility swap last. Neither sends vehicle messages.
- The private DSI adapter loaded, resolved all ten symbols, constructed, attached, registered and received registry/messages. This validates the exercised observation path, not every private ABI/lifetime path.
- Baseline, radio-selector and navigation comparison captures each completed their 15-second window, with zero malformed records, dropped records or HUD commands sent.

| Discovery window | Received messages | Distinct header patterns | Registry entries |
| --- | ---: | ---: | ---: |
| Normal HUD | 1927 | 99 | 112 |
| Radio selector | 2998 | 143 | 112 |
| Navigation instruction | 1953 | 108 | 112 |

The user confirmed each windshield view. The radio selector auto-closed, so the user pressed Mode to keep it appearing; the radio window includes those interactions. Counts are observations, not isolated proof of an overlay's protocol.

**No registry advertised 0x82/0, and the scoped observer saw no 0x82 headers.** Broad bounded observation was added to avoid assuming that generic BMW HUDTerminal is the Supra's drawing path. The client reported registration/link up and raw communication state 1; that is not proof of the upstream expected communication-state value 2 or of a healthy physical MOST drawing route.

The radio window had prominent additional 0x40/1 traffic from 0x1019 and 0x15/2 traffic from 0x5000. These are correlation candidates, not identified HUD drawing commands. No handles, dimensions, colors, payload meanings or ownership were inferred from them.

The factory NavNBTEvoController binary was captured twice, byte-identically, for offline protocol review. Its bytes remain in private Drive evidence only. This enables further investigation without keeping the car connected.

## Launcher fixes verified on the car

QNX reports `armle` through `uname -p`; `uname -m` reports the board model. The target lacks `dirname`, so launchers use shell parameter expansion. DSI dependencies need `/opt/sys/lib` in the test process's library search path; launchers set LD_LIBRARY_PATH only for that process. The initial observer attempt exited before registration because that path was absent; the corrected attempt succeeded.

`--observe-registry --all-headers` aggregates at most 256 distinct source/destination/function/operation/class patterns instead of recording individual messages. It captures no payload bytes and retains the same registration-only/no-drawing behavior. `check_session_result.py --kind discovery` accepts complete negative service evidence while leaving drawing_authorized false; the original registry gate still rejects a missing 0x82 host.

## Cleanup and remaining work

All test processes exited, the session-specific RAM-directory files and directory were removed, and the SSH master was closed. The user confirmed normal HUD/radio/navigation operation. SSH had been temporarily re-enabled for access and the server was still listening afterward; no server-disable or reboot is claimed. No persistent HUD installation, coding or firmware update was performed.

Next work is offline comparison and factory navigation/MOST code review to identify the Supra's actual HUD path. Do not turn the existing generic drawing assumptions into a live sender. Exclusive object ownership/release, geometry/palette, acknowledgement semantics, low-latency updates, overlay recovery and live telemetry calibration remain unproven. The conservative 1.95-second rendering sequence still exceeds the 300 ms production freshness budget.
