# Native v1 validation, 16 November 2026

NOT APPROVED FOR UNATTENDED INSTALLATION OR ROAD TEST.

## Passed on the actual head unit

- Native executable loads on QNX 6.5 armle.
- Isolated pre-send interposition against the fake provider returns CLEAN before its factory send, including the traced build. This is not a real navigation interception test.
- Head-unit-only RPM probe: 40 valid samples, about 650 RPM, consistent with the user's factory tachometer observation.
- Standalone drawing: 30 seconds, 120 frames; user confirmed smooth accurate RPM and no circle/arrow. All cleanup and resource checks passed; user confirmed both displays normal.
- Native cooperative yield request after five seconds: cleanup and CLEAN handshake passed; user confirmed graphics absent.

## Compatibility corrections

The actual shell lacks printf, dirname, cmp, sync and head in its normal path. /dev/shmem does not support mkdir. /tmp is backed by /fs/ram5. Scripts now use echo, shell path expansion, and verified RAM /tmp where applicable. Capture statistics must be initialized before pcap_stats: the old uninitialized structure caused monitor_unknown before any image was sent. Corrected native build passed the full live display run. An absent-variable unset returns failure on this shell, so strict launchers must explicitly tolerate that operation.

## Startup discovery and failed integration

The real controller entry is in /opt/nav/eceusa/bin/NavigationEceUsa.cfg, included by starter.cfg. Working directory /opt/nav/eceusa/bin; factory argv and environment captured privately. Initial APS partition softrt_NAV; controller initializes its main thread to 63r. Factory configuration has no automatic process restarts for this entry; this does not disable system watchdog supervision.

Two RAM-only controller replacement attempts were made. First: SIGTERM stopped the original controller, but the strict launcher exited on unset of absent variables. Neither the hooked replacement nor original-process restoration launched; the head unit restarted. The launcher defect was identified and its corrected original-environment branch was exercised harmlessly on target.

Second: corrected launcher started the replacement; memory listing confirmed the experimental library loaded, and scheduling/thread initialization matched expected settings. The head unit nevertheless restarted before real navigation interception was tested. Do not claim the hook caused the restart or that it passed. Watchdog records name the terminated original controller PIDs (229432 and 225334); exact reset cause still requires crash/log analysis. Do not repeat unmanaged controller termination as an installation method.

The independent shell restoration supervisor did NOT prove reliable recovery across the head-unit restart. It remains a failed experiment, not an accepted rollback mechanism. No persistent startup file was changed. No v1 installation or road-test approval was issued.

## Recovery and saved evidence

After both restarts the user confirmed normal HUD and iDrive. Final factory navigation in windshield and cluster, radio selector and iDrive all passed the user's visual/functional check; no test graphics remained. Final reads verified NavigationEceUsa.cfg exact bytes unchanged, original controller present, no experimental library in its memory listing, no HUD worker or trial supervisor, and no temporary supra directories after reboot. SSH client connection closed; temporary vehicle SSH was not explicitly disabled.

Private Drive evidence includes exact startup files, process/scheduling/environment records, native journals, both watchdog error reports, system-load reports, NavNBTEvoController.core, archive/lifecycle/reset history and current slog. Crash images/configuration/environment are private and must not enter this source repository.

Next work is offline analysis of watchdog registration, sanctioned controller lifecycle and the crash dump. Do not bypass/disable factory watchdogs. Then design and test startup admission and navigation resume. Sustained runtime and agreed shift thresholds remain unvalidated. The working 30-second native display is a separate passed component.
