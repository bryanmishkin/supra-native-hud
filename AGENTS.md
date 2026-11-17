# Agent entry point

**Startup reliability reopened:** a subsequent cold start was blocked by a reproduced false startup-watchdog quarantine. See [current findings and correction](docs/V1-STARTUP-FOLLOWUP.md). The earlier acceptance below records one passed cycle.

**Startup repair accepted 17 November:** automatic tachometer startup passed after a locked vehicle shutdown and normal start with ENET unplugged. Navigation/radio cleanup and automatic return then passed with machine evidence and owner confirmation. The accepted runtime uses the internal RPM gateway and rate-limited input recovery. See [exact build, evidence and limits](docs/V1-COLD-START-ACCEPTANCE.md).

This repository contains a working vehicle-specific persistent HUD tachometer and substantial earlier research. Start with [APP-STATUS.md](APP-STATUS.md), [docs/AGENT-HANDOFF.md](docs/AGENT-HANDOFF.md), [docs/APP-ARCHITECTURE.md](docs/APP-ARCHITECTURE.md), and [PERSISTENT-INSTALL.md](PERSISTENT-INSTALL.md).

- The reference installation is committed and enabled, with owner-confirmed startup after an unplugged iDrive reset on 17 November 2026. Do not treat historical “blocked” or “not installed” statements as current status.
- Installed implementation: gates → resident → native worker, using shared cluster guidance state. Earlier DSI tools and isolated-session prototypes are not this path.
- Preserve actual evidence scope: one vehicle/firmware, parked acceptance, visual unplugged warm restart. One repaired vehicle shutdown/start is now verified; repeated cycles and road endurance remain unverified.
- Read COMPATIBILITY.md before proposing another vehicle installation. Hard-coded network, model, resource and ABI values are not universal configuration defaults. Do not bypass failed identity, hash, ACK or admission checks.
- For an accepted persistent install, leave it running when requested. Do not automatically roll back at the end of a successful session.
- Keep factory captures, private profiles, generated kits/binaries, SDK/license material and credentials out of Git. Preserve exact original startup files and installer state privately for rollback.
- Update current docs when behavior or acceptance changes. Mark historical evidence as historical rather than rewriting old failures into successes. Record machine evidence and human display observations separately.
- Documentation-only changes need link/command/source consistency checks; do not connect to the vehicle or rerun live tests for prose edits.

## V2 branch

On `v2-ux`, read [docs/V2-UX.md](docs/V2-UX.md) first. V2 has explicit bounded test modes; the default persistent worker still selects V1 sport. Use docs/V2-CAR-TEST.md to pause V1 cleanly, test from RAM, then verify V1 after a normal restart. Never run both workers together or replace installed V1 files for this test. Preserve the Gold Master tag and distinguish synthetic PSI previews from live telemetry. Start within 150 × 36; larger-space experiments need separate proof.
