> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# Continuous runtime and factory handoff — 16 November 2026

Not an unattended v1 release. Factory startup is restored; no app autostart installed.

## Confirmed on the Supra

- Unarmed gate startup, one-use navigation-hook startup, and original startup restoration each passed the planned two-minute process-stability checks. Original config bytes and inode were preserved; system partition returned read-only.
- Automatic navigation handoff passed: 82 frames, factory_navigation_request, cleanup_verified=true. Hook trace recorded CLEAN before FACTORY_SEND. User confirmed normal navigation in both displays.
- Radio handoff did not pass. First run quiesced after 60 frames with cleanup unverified, although radio looked normal.
- Added explicit --continuous-parked-guidance-stopped mode with duration argument 0. It retains input freshness, traffic revocation, cooperative stop, and fail-closed transport checks. Request IDs wrap only between synchronous completed calls. Journal growth is bounded around 1 MiB by truncation at request boundaries; this is a rolling diagnostic log, not full-history retention.
- Continuous target run rendered 432 frames (approximately 108 seconds). User confirmed smooth readable RPM without symbols or flashing. User then opened the radio selector; worker stopped on factory activity with cleanup_verified=false. User reported tachometer remained visible after selector closed. Both custom bitmap slots were still allocated. This is a real cleanup failure, not a duration timeout.
- User performed normal restart. All ten tested bitmap slots were then absent; original config, hook absence, worker absence, RAM-state removal and read-only mount verified. User checked navigation, radio, both displays and iDrive: all normal, no test graphics.

## Code and evidence

The HmiMain3D executable was captured privately. It imports the SomeIP adapter variant using std::weak_ptr, whereas the navigation controller uses TWeakPtr. Added a separate opaque-reference interposer entry point for that ABI. Both ABI variants pass nine isolated Linux hook cases, including CLEAN-before-send and timeout behavior. QNX cross-build passes. This new HMI entry point is NOT loaded or target-validated; observing the imported symbol does not prove coverage of every radio send or establish a safe HMI startup route.

Eleven standalone loopback integration cases pass, including continuous stop and request-ID wrap. The deployed continuous executable hashes are saved separately from the later build.

## Remaining installation work

1. Validate the HMI-side pre-send hook under its factory startup supervisor and prove radio cleanup before the factory send; do not live-kill/replace HMI.
2. Establish authoritative navigation AND radio release signals. Silence, an expired timer, or one guidance-idle packet is insufficient to claim the shared renderer is released. Automatic return remains unimplemented.
3. Add and validate persistent app startup/standby/admission, restart behavior and fault recovery, then longer unattended operation. Continuous mode alone does not meet this requirement.

Candidate executable/profile/control files remain at /var/opt/supra-hud/continuous-candidate, without a startup entry. Prior consumed boot-trial files are inert under the restored original config. No v1 installation or automatic return is claimed.
