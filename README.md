# Supra native HUD tachometer

**V2 development branch:** [UX candidate and preview](docs/V2-UX.md), including accepted V1 startup/recovery fixes from `377d3fe`. V2 now has an audited RAM-only test candidate and opt-in pressure reader; the installed/default persistent worker remains V1. Follow the [V2 car-test runbook](docs/V2-CAR-TEST.md).

**Startup reliability reopened:** a subsequent cold start was blocked by a reproduced false startup-watchdog quarantine. See [current findings and correction](docs/V1-STARTUP-FOLLOWUP.md). The earlier acceptance below records one passed cycle.

**Startup repair accepted 17 November:** automatic tachometer startup passed after a locked vehicle shutdown and normal start with ENET unplugged. Navigation/radio cleanup and automatic return then passed with machine evidence and owner confirmation. The accepted runtime uses the internal RPM gateway and rate-limited input recovery. See [exact build, evidence and limits](docs/V1-COLD-START-ACCEPTANCE.md).

A native QNX application that adds live RPM, a segmented tachometer bar, and orange/red shift lights to the factory windshield HUD. It runs on the head unit without a connected Mac. It yields to factory navigation and the radio selector, removes its graphics, and returns when both factory functions are explicitly idle.

**Installed and enabled on the reference Supra on 17 November 2026.** Automatic startup, navigation/radio handoff and return, verified cleanup, and a five-minute uninterrupted run passed. The owner confirmed automatic startup after a further iDrive reset **with the ENET cable unplugged**. See [verified status and limits](APP-STATUS.md) and [installation evidence](PERSISTENT-LIVE-VALIDATION.md).

The reference vehicle is a **2026 Toyota GR Supra 3.0 Premium, six-speed manual**, NBT Evo **NBTevo_T24081I**, QNX 6.5 ARM. This is one verified vehicle/firmware combination, not a universal BMW/Supra installer. The drawing path shares factory guidance state; it is not an independent overlay surface. One repaired vehicle shutdown/start is verified; repeated overnight cycles and road endurance remain unverified.

## Start here

| Need | Read |
| --- | --- |
| Pick up the project as an agent | [AGENTS.md](AGENTS.md), then [agent handoff](docs/AGENT-HANDOFF.md) |
| Understand what is proven | [APP-STATUS.md](APP-STATUS.md) |
| Understand the app and drawing path | [App architecture](docs/APP-ARCHITECTURE.md) |
| Build and test offline | [Build environments](environment/README.md) |
| Install, validate, disable or restore factory startup | [PERSISTENT-INSTALL.md](PERSISTENT-INSTALL.md) |
| Investigate a missing/stopped display | [Operations and recovery](docs/OPERATIONS.md) |
| Evaluate another vehicle | [COMPATIBILITY.md](COMPATIBILITY.md) |
| Find older protocol research or test evidence | [Documentation index](docs/INDEX.md) |

## What the installed app does

- Renders the sport layout inside the measured **150 × 36** bitmap: large RPM digits, 24 bar segments and five steady shift lights.
- Reads actual engine RPM through the diagnostic gateway, targeting one display update every **250 ms**. It does not command engine speed.
- Uses the verified symbol-free graph and alternating bitmap resources to avoid the former circle/arrow and flashing.
- Starts only after a minimum 30-second resident settling period **and** acknowledged idle states for navigation and radio.
- Stops drawing for factory navigation/radio, verifies removal, then resumes automatically after acknowledged release.
- Stops automatic operation on uncertain drawing state. A normal process exit alone is not proof that remote graphics disappeared.

The current code uses a 7000 RPM display scale and 6500 RPM full shift cue. These are display settings, not validated engine limits. Boost, user-adjustable settings, an independent windshield-only surface, and general vehicle support are not implemented in the installed path.

## Build and source availability

[Build instructions](environment/README.md) distinguish ordinary host tests from the QNX ARM build and profile-dependent integration tests. The repository contains source, not a ready-to-install public binary release. A compatible ARM-capable QNX SDK, target runtime audit inputs, and a verified private drawing profile are separate prerequisites.

The installed path is `persistent_boot_gate.c` → `supra_resident.cpp` → `supra_standalone.cpp`, with `navigation_handoff_hook.cpp`, `factory_lease.*`, `factory_stream.*`, `standalone_wire.*` and `tach_bitmap.*`. Older DSI/registry encoders and Mac-driven trial tools remain research code; they are not the installed renderer.

Vehicle captures, factory binaries, generated kits, SDKs, credentials and license material stay outside GitHub. See [third-party notices](THIRD_PARTY_NOTICES.md); this documentation does not add a license grant for the original project source.
