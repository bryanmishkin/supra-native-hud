# Pick up this project

**Cold-start issue reported 17 November:** the owner saw no tachometer after a cold vehicle start. Prior warm-reset acceptance remains valid but does not establish cold-start reliability. This branch contains an offline-tested repair candidate; the actual saved blocker is `factory transport closed`. The narrow repair is installed on the reference car; post-repair cold-start acceptance is pending. See [failure, evidence and exact repair plan](V1-COLD-START.md).

## Current baseline

Accepted executable source: `fd55e97`, private persistent kit revision08, manifest SHA-256 `84e5233be33e68bf305028cdb232d6e49f2f939af702ab69d44134768859078a`. Later documentation commits describe the same accepted binaries unless explicitly stated otherwise. Installed and enabled on the reference Supra; owner confirmed the final unplugged reset worked.

Read in order: [status](../APP-STATUS.md), [architecture](APP-ARCHITECTURE.md), [compatibility](../COMPATIBILITY.md), [build](../environment/README.md), [installation](../PERSISTENT-INSTALL.md). [Documentation index](INDEX.md) identifies historical material.

## Decisions already resolved

- Working transport is cluster Ethernet guidance, not the absent DSI HUD registry service.
- A create call did not produce an independent usable drawing surface. Use the documented shared-session model with factory priority; do not dispose instance 200.
- RLE32 bitmap upload and removal work. The symbol-free combination is empty high-guiding union plus direction 0, retaining the coming-road image.
- Smooth updates use two bitmap slots and change only the image binding each frame. Rebuilding the full graph caused flashing.
- The red/blue boundary mapping is necessary for the tested target. Do not remove it because an offline canonical BGRA preview looks correct.
- Both factory writers need pre-send coverage. Passive detection alone arrived too late for safe shared-state cleanup during radio takeover.
- Automatic return comes from observed successful idle commits for both lanes, not a quiet timer or a worker restarting itself.
- Factory startup uses same-PID exec gates and preserves the exact HMI graphics preload. Manually replacing supervised processes caused prior restarts and is not the install method.
- Target startup required a minimum settling delay, narrow handling of unused startup connections, and clean-exit/pre-admission race fixes. These are implemented and regression-tested.

## Private prerequisites and evidence

GitHub intentionally does not contain the installable private profile, original factory images, target runtime libraries, SDK or binary kit. Do not claim a fresh clone alone can install another car. For the reference installation, obtain the owner's existing private validation bundle and retain its installer state; do not recapture everything by default.

The evidence bundle is titled **Supra HUD — Persistent Install Live Validation — 2026-11-17.zip** in the owner's Drive. It includes the private kit, original/readback material, acceptance logs, failed candidate evidence and source archive. Access is owner-specific; do not assume another agent/account can retrieve it. The GitHub validation report summarizes what is known without redistributing proprietary bytes.

If access is unavailable, state exactly which artifact is missing and continue independent source/offline work. For another vehicle, use its own baseline and complete the compatibility matrix; do not borrow the reference originals as rollback data.

## How to make the next session productive

Prepare builds, hashes, kit, expected observations and rollback before requesting car time. Capture baseline, startup, navigation/radio takeover and return, continuous operation and final state in one coordinated session where possible. Distinguish a temporary diagnostic connection from the app's persistent state. Save each checkpoint before another restart overwrites RAM evidence.

An agent should be able to answer before deployment: Which exact candidate? Which target bytes? Which shared resources? What proves removal? What permits automatic return? How does normal startup activate it? What exact originals restore factory startup? What remains untested?

Do not request another discovery session for facts already established on this target. New-target adaptation, cold sleep/wake and endurance are legitimate separate work; they are not completed merely by the unplugged warm restart.

## Documentation maintenance

APP-STATUS is the current claim table. APP-ARCHITECTURE explains code. PERSISTENT-INSTALL owns execution/rollback procedure. PERSISTENT-LIVE-VALIDATION owns the reference acceptance record. Historical reports retain their original observations and should not be used as current install instructions. When implementation changes, update these current documents together and retain the prior acceptance revision so rebuilds are not mistaken for already-tested binaries.
