# MOST diagnostic preparation

18 November 2026. Offline preparation only. No vehicle connection, installation, diagnostic requests or factory changes performed. Owner requested preparation for a MOST diagnostic tool; exact tool choice is awaiting clarification.

## Available mechanisms are not interchangeable

| Mechanism | Evidence and scope | Limit |
| --- | --- | --- |
| Existing `supra-registry-observer-qnx --observe-registry --all-headers` | Source subscribes to the DSI registry and logs received message headers for 15 seconds; 20-second deadline. No device-control keys or target function calls. | Temporary DSI client/subscriptions; not a physical MOST-bus sniffer, not guaranteed to receive traffic addressed to other clients, and no payloads. Absence of a HUD entry does not prove no physical HUD route. |
| Installed V1 EngineSpeed2 | DSI/MOST Vehicle 05/00, function 0cd0, provider 5000 on this reference vehicle. | RPM source only; no independent drawing-surface discovery. Leave installed V1 unchanged. |
| inotbarnacle MOST diagnostic tunnel | Current public tree pinned to d0df14ac6d394bd2bf29caa6cf2dc5b9ab1fe87b. `source/native/src/most/most_link.c` uses FBlock 06/F0, function 050, routine 0F0B, diagnostic source 63. | ECU request transport, not a general MOST/HUD sniffer. Documentation establishes only a DME route on the author's different vehicle; not Supra receiver support. |

Public source reference: https://github.com/inotbarnacle/ID6_apps_prerelease/blob/d0df14ac6d394bd2bf29caa6cf2dc5b9ab1fe87b/source/docs/MOST.md

The tree has no separately named MOST diagnostic executable/package. Identify the specific tool before selecting its modes or calling it ready. Credit inotbarnacle for the diagnostic tunnel and the existing NBT-AAD authors for the vendored MOST client. Preserve their respective licenses; do not assume one package's license covers all packages.

## Prepared parked-session procedure

1. Record exact tool/source/build/hash and verify supported QNX/DSI ABI against saved target evidence. Use the already installed V1 baseline for before/after comparison. Do not install a dashboard suite to obtain one tool.
2. Retrieve V1 persistent faults and runtime evidence before any reset, especially after the owner's longer drive. Do not use this preparation as permission to reset or erase the failure.
3. Start with service inventory using an isolated, bounded temporary client. Record client identity, registry keys/provider addresses, link state, missing or dropped entries, time interval and exact commands.
4. For HUD research, require evidence of a relevant service and documented read-only inspection before any targeted request. Do not register a drawing/control target, change notification routing or send arbitrary function IDs to see what happens.
5. If the intended tool is the diagnostic tunnel, limit its proposed initial scope to a reviewed, known read request to a proven target. Do not start ECU routine sweeps, clears, actuator controls, coding, programming, session/security changes or generic polling. The tunnel's routine envelope is itself an active request even when its inner operation reads data; describe it accurately.
6. Bound runtime/output; retain errors and raw evidence privately. Confirm temporary client/process cleanup and V1 health. An observer process exit does not by itself prove every server-side registration was removed; retain that limitation until verified.

No tool-specific deployment command is approved by this document. The tool selection and its actual available modes remain to be verified. No car action is needed while the owner is driving.
