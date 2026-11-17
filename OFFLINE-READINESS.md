> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

> On-car update, 16 Nov 2026: the loader, ten self-tests, replay and registry/overlay observations now pass. The expected 0x82/0 HUD service was absent in every window. See CAR-VALIDATION.md for measured results and cleanup. Earlier planned checks below are retained as procedure/history, not outstanding execution tasks. Live drawing remains blocked on actual Supra transport discovery.

# Offline readiness

Completed: source implementation, 32/64-bit host tests, QNX ARM builds, static candidate dependency/import checks, DSI required-symbol/table-size check, bounded target self-test, header-only registry observer, local result validator and a hash-checked car-kit packager.

The next trip should verify the new executable/runtime path before attempting private DSI observation. Prior runtime captures are already complete enough for the current static checks; repeat them only if identity/hash comparison or a loader error identifies a change or gap.

The build directory contains candidates, not an installable live dashboard. Core/native sequencing is tested, but the live sender, object acquisition/release, Supra profile, factory overlay mapping and live telemetry binding still require verified car behavior. The present 40-call rendering strategy cannot meet the default 300 ms freshness budget at conservative 50 ms pacing; frame expiry now enforces that limit.

The source repository excludes generated binaries, captured OEM libraries, SDK and license material, credentials and session logs. Those boundaries do not prevent host tests or source review. Prepared binaries, exact hashes and complete evidence remain in Drive.

Follow NEXT-CAR-SESSION.md. A car-session success means explicit evidence was collected and validated; it does not mean untested live drawing is ready.
