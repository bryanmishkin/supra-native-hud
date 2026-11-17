# Agent entry point

**Cold-start issue reported 17 November:** the owner saw no tachometer after a cold vehicle start. Prior warm-reset acceptance remains valid but does not establish cold-start reliability. This branch contains an offline-tested repair candidate; the actual saved blocker is `factory transport closed`. The narrow repair is installed on the reference car; post-repair cold-start acceptance is pending. See [failure, evidence and exact repair plan](docs/V1-COLD-START.md).

This repository contains a working vehicle-specific persistent HUD tachometer and substantial earlier research. Start with [APP-STATUS.md](APP-STATUS.md), [docs/AGENT-HANDOFF.md](docs/AGENT-HANDOFF.md), [docs/APP-ARCHITECTURE.md](docs/APP-ARCHITECTURE.md), and [PERSISTENT-INSTALL.md](PERSISTENT-INSTALL.md).

- The reference installation is committed and enabled, with owner-confirmed startup after an unplugged iDrive reset on 17 November 2026. Do not treat historical “blocked” or “not installed” statements as current status.
- Installed implementation: gates → resident → native worker, using shared cluster guidance state. Earlier DSI tools and isolated-session prototypes are not this path.
- Preserve actual evidence scope: one vehicle/firmware, parked acceptance, visual unplugged warm restart. Cold sleep/wake and road endurance remain unverified.
- Read COMPATIBILITY.md before proposing another vehicle installation. Hard-coded network, model, resource and ABI values are not universal configuration defaults. Do not bypass failed identity, hash, ACK or admission checks.
- For an accepted persistent install, leave it running when requested. Do not automatically roll back at the end of a successful session.
- Keep factory captures, private profiles, generated kits/binaries, SDK/license material and credentials out of Git. Preserve exact original startup files and installer state privately for rollback.
- Update current docs when behavior or acceptance changes. Mark historical evidence as historical rather than rewriting old failures into successes. Record machine evidence and human display observations separately.
- Documentation-only changes need link/command/source consistency checks; do not connect to the vehicle or rerun live tests for prose edits.
