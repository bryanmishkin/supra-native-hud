# Current V1 baseline — 18 November 2026

Baseline tag: `v1-baseline-2026-11-18`. This is the current installed and enabled reference-car version. The owner unplugged after the passing drive. No vehicle changes were made during baseline promotion. The original `v1.0.0-gold-master` tag is historical and unchanged.

## Exact installed identity

| Component | SHA-256 | Application source |
| --- | --- | --- |
| `supra-standalone-parked-qnx` | `5be8a000f7d8d0561a3c7b1d2043d1be5bce88af5d68cbc66c7be5189f232274` | `db214b5` |
| `supra-resident-qnx` | `7396aaaf9ddfd58011c5cde875f8f4df332a41bdbad1a1cb984aa7a590446595` | `32da565` |

The exact private package manifest hashes to `ac903624ebda36039885a2d2fb36cc3f5d9403f22b554d448ab8ae584268c6c7`. [Machine-readable component inventory](V1-BASELINE.json) lists every packaged hash. Later documentation commits do not imply rebuilt binaries. A fresh rebuild must be audited and compared; do not substitute it for the archived installed bytes.

Reference: 2026 Toyota GR Supra 3.0 Premium six-speed manual, NBT Evo `NBTevo_T24081I`, QNX 6.5 ARM. Shared guidance session 200, 150 × 36 bitmap. Not a generic installer or an independent HUD surface.

## What this version does

- Runs natively on the head unit with the factory EngineSpeed2 RPM feed through DSI/MOST; no laptop or diagnostic gateway RPM relay.
- Preserves the smooth symbol-free V1 sport layout and corrected orange/red shift lights.
- Creates/removes only bitmap slots `0x01000008` and `0x01000009`; startup does not require factory slots 0..7 to be empty.
- Gives factory navigation/radio priority through acknowledged admission and cooperative cleanup. Narrow, exact-byte-authorized background traffic can coexist; unknown traffic is not ignored.
- Retries verified-clean RPM input failures and zero-frame owned-slot contention with bounded backoff. Uncertain cleanup, transport or unrecognized failures remain quarantined.
- Preserves first and four recent fault records in persistent storage. RAM journals still rotate; collect both before resetting.

## Verified on this exact baseline

Owner confirmed tach visible after restart and no visible loss on the subsequent drive. Post-drive read-only capture matched all 15 installed binary/configuration comparisons. The supervisor was healthy and drawing, with seven worker starts and six clean factory handoffs. Both current retry counters were zero; all permanent fault records were unchanged from before the drive. Frames advanced from 604 to 622 during collection. See [drive record](OWN-SLOTS-DRIVE-RESULT.md).

The permanent writer was verified on the target and its isolated proof record survived an iDrive restart byte-for-byte. Earlier versions established native RPM, color/layout, cleanup and navigation/radio return; those are historical component evidence, not new tests of every final combination.

Not established: overnight or repeated cold-start cycles on this exact final worker/supervisor combination, extended endurance, every assistance/warning interaction, other vehicles/firmwares or an independent windshield-only surface. Prior cable-free startup passes involved earlier workers and must not be relabeled final-build cold-start acceptance. No stability-control attribution was proven.

## Private build and rollback package

Owner Drive archive: **Supra-HUD-V1-Current-Baseline-2026-11-18.zip**. It contains:

- `installed/`: exact final component bytes, profile, manifest and original/modified factory startup configurations.
- `rollback/prior-installed-package/`: complete package immediately before the own-slot worker change. It is a known fallback with the previous suppression limitation, not a claim of better behavior.
- `rollback/original-install/`: original installer state and its matching kit, retained for the factory-restore workflow.
- `evidence/`: installation receipts/readbacks, pre/post-restart capture, passing drive and test reports.
- `source.tar.gz`, baseline documentation and SHA-256 inventory.

The original factory executables were never replaced. `installed/nav-before.cfg` and `installed/system-before.cfg`, together with the verified transaction tools and original installer state, support restoring factory startup. Keep exact reference-car files private and never apply them blindly to another car. Consult [installation and rollback](../PERSISTENT-INSTALL.md) before either code rollback or full factory restoration. Never copy old activation tokens or overwrite persistent fault evidence as part of rollback.

## Agent pickup

Read this file, [architecture](APP-ARCHITECTURE.md), [operations](OPERATIONS.md), [installation](../PERSISTENT-INSTALL.md) and [compatibility](../COMPATIBILITY.md). Use the exact archived kit as the comparison baseline. Capture before resetting; do not delete `disabled` as a diagnosis. No new car session is needed to reconstruct the facts already captured. V2 is a separate branch and has not automatically inherited these final V1 changes.
