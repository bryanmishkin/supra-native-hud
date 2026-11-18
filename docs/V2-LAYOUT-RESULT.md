# V2 layout test — 18 November 2026

**Layout accepted visually; V2 removed; exact V1 baseline restored and verified.** The reference car was parked outdoors with the engine running. No pressure probe or boost mode ran, and no persistent installation files or enable/disable tokens were changed.

## Observed results

| Run | Machine evidence | Owner observation |
| --- | --- | --- |
| Initial 30 seconds | 140 frames, duration_complete, cleanup verified, shared instance preserved; recorded RPM 646–669 | Looked okay, but timed removal occurred before the owner could check RPM response |
| Extended layout-only | Configured for 120 seconds; cooperatively stopped at owner request; 424 frames, 91.220 seconds between first/last logged RPM samples; observed RPM 628–6970; CLEAN acknowledgment and verified cleanup | Smooth and readable; colors look right; owner requested return to V1 |

The longer run was **not a full two-minute endurance pass**. The cooperative stop uses the worker's `factory_navigation_request` reason, but was initiated by the control client at the owner's request, not by a factory navigation action. No new navigation/radio takeover test was performed. Both runs recorded zero pressure-response records and zero boost-visible frames.

## Candidate identity and tooling correction

Initial worker: `6b8653c2728be49aae49c25853ba951890fdd80d32184cdb96499734e6a338a5`.

Extended worker: `51a0fcc4f2bc5915e1f4191d9fa1c9672a4d8a4e2997347488dd89d8a09db81a`.

The extension changes only the explicit layout-mode duration ceiling to 120 seconds. Default duration remains 30 seconds; boost remains capped at 30 seconds. QNX build/static target audit, duration-rejection checks, factory-feed cleanup checks and six runner unit tests passed.

The first runner attempted to parse all stdout as JSON; native DSI startup messages preceded the successful terminal result. It now uses V1's strict known-preamble parser. The saved first result was independently parsed and reconciled; no repeat drawing was needed to establish its cleanup. The second run's automated full-window gate remains false because the owner ended it early. Raw outcomes are preserved rather than relabeled timed passes.

## V1 restoration

The owner initially selected a restart/waiting response but later clarified that the restart had not yet been performed. While V1 was still intentionally paused, its stopped RAM state was archived after confirming no resident/worker processes or control sockets. That was unnecessary for the subsequent full restart; it did not change persistent startup. **No reset-persistence failure was established.**

After the actual owner-operated iDrive restart, the owner confirmed V1 was back. The runner verified:

- Temporary V2 directory absent.
- Exact installed binaries/profile/startup files match the current V1 baseline; enabled token and read-only filesystem protection intact.
- Both factory hooks present; supervisor healthy, available and not quarantined.
- Heartbeat, RPM frame counter and sample timestamp advancing.
- Final status: one worker start, worker running, no clean stops on the fresh boot.
- All five persistent fault files byte-identical to pre-test copies.

The user was told they could unplug only after this verification passed. V2 is not persistently installed. Positive boost, V2 automatic return, expanded drawing space and road endurance are outside this session's acceptance.

Private evidence directory: `v2-layout-live-2026-11-18`. Retain both kits, build/audit records, numbered command output, raw worker results, owner observations, summarized RPM samples, and before/after V1 captures.
