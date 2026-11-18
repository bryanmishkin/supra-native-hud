# Supra native HUD tachometer

**V2 development branch:** the [visual test candidate](docs/V2-CAR-TEST.md) includes the current V1 baseline fixes. It is a RAM-only layout trial; the installed V1 remains unchanged. Live boost is a separate experimental mode.

A native QNX application that adds live RPM, a segmented tachometer bar, and orange/red shift lights to the factory windshield HUD. It runs on the head unit without a connected Mac. It yields to factory navigation and the radio selector, removes its graphics, and returns when both factory functions are explicitly idle.

**Current V1 baseline: [`v1-baseline-2026-11-18`](docs/V1-BASELINE.md).** Installed and enabled on the reference 2026 Toyota GR Supra 3.0 Premium six-speed manual, NBTevo_T24081I / QNX 6.5 ARM. The final build passed restart and one owner-confirmed no-visible-loss drive, with no new permanent fault records. Six clean factory handoffs occurred. Repeated overnight cycles and extended endurance on this exact build remain unverified.

[Exact installed hashes and rollback package](docs/V1-BASELINE.md) are authoritative. Original `v1.0.0-gold-master` remains historical and unchanged. This shares factory guidance state; it is not a universal installer or independent HUD surface.

<p align="center"><img src="docs/assets/v1-layout.png" width="750" alt="V1 tachometer software preview: RPM, segmented bar and shift lights"></p>

*Actual V1 renderer at a simulated 6200 RPM, enlarged 5× for illustration. This is a software preview, not a windshield photograph; the vehicle bitmap is 150 × 36 pixels.*

**[Download compiled V1](https://github.com/bryanmishkin/supra-native-hud/releases/tag/v1-baseline-2026-11-18)** · **[Equipment & setup](docs/GETTING-STARTED.md)** · **[Install & rollback](PERSISTENT-INSTALL.md)** · **[Current verification](APP-STATUS.md)**

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
- Reads actual engine RPM through the factory EngineSpeed2 DSI/MOST feed, targeting one display update every **250 ms**. It does not command engine speed.
- Uses the verified symbol-free graph and alternating bitmap resources to avoid the former circle/arrow and flashing.
- Starts only after a minimum 30-second resident settling period **and** acknowledged idle states for navigation and radio.
- Stops drawing for factory navigation/radio, verifies removal, then resumes automatically after acknowledged release.
- Stops automatic operation on uncertain drawing state. A normal process exit alone is not proof that remote graphics disappeared.

The current code uses a 7000 RPM display scale and 6500 RPM full shift cue. These are display settings, not validated engine limits. Boost, user-adjustable settings, an independent windshield-only surface, and general vehicle support are not implemented in the installed path.

## Build and source availability

[Build instructions](environment/README.md) distinguish ordinary host tests from the QNX ARM build and profile-dependent integration tests. The release includes the exact compiled QNX ARM application components used on the reference car, their SHA-256 checksums, and notices. Installing these prebuilt components does not require a compiler. The public ZIP is **not a complete vehicle installation kit**: a verified private drawing profile, the target's own startup configurations and runtime audit are still required. Never reuse another vehicle's factory configuration blindly.

Building from source requires a compatible ARM-capable QNX SDK and target audit inputs. The full reference-car installation and rollback package is preserved privately by the owner; it is intentionally excluded from the public runtime download.

The installed path is `persistent_boot_gate.c` → `supra_resident.cpp` → `supra_standalone.cpp`, with `navigation_handoff_hook.cpp`, `factory_lease.*`, `factory_stream.*`, `standalone_wire.*` and `tach_bitmap.*`. Older DSI/registry encoders and Mac-driven trial tools remain research code; they are not the installed renderer.

Vehicle captures, factory binaries, generated kits, SDKs, credentials and license material stay outside GitHub. See [third-party notices](THIRD_PARTY_NOTICES.md); this documentation does not add a license grant for the original project source.
