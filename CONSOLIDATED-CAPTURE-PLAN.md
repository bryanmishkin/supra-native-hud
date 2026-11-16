# Consolidated capture evidence plan

The previous sessions completed individual capture lists but did not close the full project's evidence gaps. Do not describe list completion as project-wide capture completeness. Minimize user trips by completing the offline work and instrument validation below before proposing another session.

## Coverage audit, 16 November 2026
Across the audited private capture directories: 38 unique ELF binaries; 19 unique binaries in the resolvable NavNBTEvoController DT_NEEDED closure; no conflicting versions among matched dependency names. Four missing direct/transitive names: libicudata.so.46, libicui18n.so.46, libicuuc.so.46, libsys_icu46_collation.cpp-ne.so. These are ICU/text dependencies; absence is not by itself evidence of a HUD blocker. The audit excludes dlopen plugins and cannot prove runtime versions.

NavigationBasic and NavigationFully are not captured in those roots, although both run alongside NavNBTEvoController and their paths/sizes were listed on the car. Likewise the SOME/IP discovery daemon and enhanced testability server binaries are not captured. Search all existing archives before requesting duplicates. Treat provider ownership as unresolved rather than assuming NavNBTEvoController is the whole implementation.

## One-session evidence matrix
| Question | Consolidated evidence to collect if still needed | Completion check |
| --- | --- | --- |
| Which process provides ManeuverView? | Current process arguments, targeted full mapped-library lists for navigation processes, service-broker/provider binding evidence through a verified read-only query | Exact service-to-process association, or an explicit unresolved result; a string match alone fails |
| Is provider code available offline? | NavigationBasic and NavigationFully at the already observed /opt/nav/eceusa/bin paths; mapped provider libraries not already captured | Full-size double-read hashes; ELF identity; dependency inventory; include configuration files referred to by actual arguments |
| How is guidance created and destroyed? | Continuous timestamped capture covering the actual RIC create/initialize/dispose lifecycle, with all relevant cluster peers and ports and SOME/IP discovery | Method 1 request AND matched response; subsequent returned handle usage and disposal where observable; no drops, no gaps, captured transition confirmed |
| What does DisplaySink select? | Same continuous capture through normal/radio/navigation transitions, synchronized action markers and before/after state | Switch event/completion fields correlated to visible behavior without assuming their meaning from a single sample |
| What is the native graphics alternative? | Provider binding, supported service contract and runtime-selected renderer information | Establish whether independent drawable content exists; do not substitute MOST commands, factory handles, model objects or switch events for surface ownership |

## Offline gates before another trip
- Trace the guidance create request structure, response conversion and calling state machine in the already captured binary.
- Resolve the upper-level DisplaySink consumer and whether the pair of u16 fields means geometry, IDs or something else.
- Determine when factory RIC creation occurs. Starting route guidance did not capture creation in the existing windows. Do not prescribe that same action as sufficient. A startup capture may be required, but SSH activation timing and capture startup must be worked out first; do not improvise a reboot or service restart in the car.
- Prepare and test one resumable capture runner with a private manifest, already-captured-file skip checks based on hashes, per-file limits, deadline/space estimates, failure accounting and a final evidence-matrix report. The current three-file tool is not that runner and must not be represented as such.
- Validate event-timestamp retention and protocol checks offline against saved captures. Reassembled per-direction streams alone do not establish cross-direction timing. Plan continuous transition recording rather than separate uncorrelated short clips.
- Preflight the full plan with realistic transfer-size/time estimates. Ask the user for one parked session only when the remaining requested actions and expected evidence are concrete.

## Meaning of session completion
Before saying the session is complete: verify hashes, parse every required stream, check packet loss/truncation, evaluate each matrix row, preserve raw evidence, confirm cleanup and factory behavior, and clearly state any missing evidence while the user is still connected. Save a local verified copy before release; cloud upload can finish without the car. Report “all available files captured” separately from “allocation question answered.” No promise of a final trip is justified until the remaining lifecycle evidence can actually be obtained.

Current status: the consolidated runner and continuous recorder are implemented, tested and QNX-built. See STARTUP-AND-CONSOLIDATED-RUNBOOK.md for the static connection trigger, retained-HU capture candidate, automatic evidence gates and the unresolved full cold-boot limitation. The historical offline gates above describe the original plan; the runbook records their current status. No car session was performed in this update.
