# Equipment and setup

This guide prepares you for the **Supra native HUD tachometer**. Start with the [current baseline](V1-BASELINE.md) and [compatibility record](../COMPATIBILITY.md). The verified reference is a 2026 Toyota GR Supra 3.0 Premium six-speed manual with NBT Evo `NBTevo_T24081I`. Compatibility with another car must be established before installation.

## What to have ready

| Item | Purpose |
| --- | --- |
| BMW/Supra **OBD-II to ENET Ethernet cable** | Connects the car's diagnostic port to the computer's Ethernet port. A generic USB OBD reader is not interchangeable. |
| USB-C or USB-A Ethernet adapter, if needed | Required only if the computer has no Ethernet socket. |
| Laptop with a working SSH client | Transfers files, checks the target and runs installation/rollback tools. |
| Authorized SSH access to the head unit | ENET connectivity alone does not enable SSH. Establish supported access separately. |
| Compiled runtime package and checksums | Obtain from the [V1 release](https://github.com/bryanmishkin/supra-native-hud/releases/tag/v1-baseline-2026-11-18). |
| Target-specific installation inputs and backups | Verified drawing profile, runtime audit, original startup files and installer state; see [installation](../PERSISTENT-INSTALL.md). These are not included in the public ZIP. |

The laptop and ENET cable are installation/diagnostic equipment. The app runs on the head unit afterward and reads the factory RPM feed without either connected. A QNX compiler is needed only to rebuild the source, not to use the supplied binaries.

## Cable and screenshot reference

[Sq00ky / Supra-iDrive6-Android-Auto — installation guide](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/main/install.md) is a useful illustrated reference for the same NBT Evo environment. Its **Hardware Requirements for Self Service Install** section links an ENET cable and optional Ethernet adapter; later sections show the SSH utility, head-unit discovery and file-transfer preparation. Cable photos are available through its linked hardware listings.

Credit belongs to that project and its contributors. We link to their illustrations rather than redistribute them. Their Android Auto binaries, phone/CarPlay requirements, flash-drive workflow, firewall changes and installation commands are **for their app**, not instructions to install this tachometer. The upstream guide was checked on 18 November 2026; external tools and listings may change.

## Connection sequence

1. Park the car. For live engine tests, use an outdoor location; software transfer and initial inspection can use an awake head unit with the engine off.
2. Connect the ENET cable to the car's OBD-II diagnostic socket, then Ethernet to the laptop (through the adapter if needed).
3. Check the Ethernet link, assigned address and route. Discover this vehicle's head-unit address; do not assume an address from a screenshot is yours.
4. Verify authorized SSH access. A refused SSH connection is not proof of a defective cable; record the exact result before changing anything.
5. Compare firmware/runtime and prepare the target-specific kit, backups and rollback path using [PERSISTENT-INSTALL.md](../PERSISTENT-INSTALL.md).
6. Follow its staged installation and validation. Keep the vehicle parked during deployment. Check startup, cleanup, factory priority and automatic return before accepting an installation.
7. Validate a normal shutdown and cable-free start separately from an iDrive reset. Preserve the exact installed hashes and results.

## What a successful install looks like

The tachometer starts automatically once the head unit is ready and factory navigation/radio have acknowledged idle. The current app enforces a minimum 30-second settling interval; this is not a guaranteed time from pressing the engine-start button. RPM should update smoothly with no circle or arrow. Factory navigation and the radio selector take priority, and the tachometer returns after their release.

For a missing or stopped tach, [collect logs before resetting](OPERATIONS.md). Do not erase fault records or repeatedly re-arm an unexplained failure. [APP-STATUS.md](../APP-STATUS.md) distinguishes observed results from remaining validation limits.

## Download contents and limits

The public runtime ZIP includes the native worker, resident supervisor, startup/transaction helpers and navigation handoff library. Its manifest contains file hashes and source provenance. Verify `SHA256SUMS` after extracting it. Keep `THIRD_PARTY_NOTICES.md` and the bundled upstream license with the binaries.

A source ZIP from GitHub is not a compiled application. Conversely, the compiled runtime ZIP alone is not a universal installer: do not copy it onto an unaudited vehicle and assume startup routing, drawing resources or cleanup are compatible. Original project files have no additional blanket public license grant; see [notices](../THIRD_PARTY_NOTICES.md).
