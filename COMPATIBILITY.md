# Compatibility and installing on another vehicle

**Cold-start issue reported 17 November:** the owner saw no tachometer after a cold vehicle start. Prior warm-reset acceptance remains valid but does not establish cold-start reliability. This branch contains an offline-tested repair candidate; the actual vehicle fault is not yet confirmed and the repair is not installed. See [failure, evidence and exact repair plan](docs/V1-COLD-START.md).

**Verified target:** one 2026 Toyota GR Supra 3.0 Premium six-speed manual, NBT Evo NBTevo_T24081I, QNX 6.5 ARM little-endian. The owner confirmed the installed tachometer starts after an unplugged iDrive reset. This establishes independence from the Mac, not universal compatibility or cold-wake reliability.

The repository is sufficient to understand and build the source with an appropriate SDK. It is **not a self-contained generic installation kit**: factory captures, runtime libraries and the measured drawing profile are private inputs. The current installer pins exact images; it does not discover or adapt another firmware.

## Target assumptions to verify

| Contract | Current implementation | Where it is enforced or used |
| --- | --- | --- |
| CPU/OS | QNX 6.5 ARM32 little-endian; reviewed loader `/usr/lib/ldqnx.so.2` | ELF audit, live identity, target execution |
| Head-unit local IP | `169.254.199.119` | Resident child arguments; installer `--head` only changes SSH destination |
| RPM gateway | `169.254.106.96:6801`, tester `0xf4`, ECU `0x12`, PID 0C | `tools/supra_standalone.cpp` |
| Cluster and internal interface | `160.48.199.96:30502`, `vlan73` | Resident, worker, hook and stream classifier |
| Guidance/list contracts | services `0xb006`/`0xb00e`, instances `200`/`100`, reviewed visibility models | Lease, wire encoder and profile |
| Resource pool and geometry | IDs `0x01000000`–`0x01000009`; app uses last two; 150 × 36 | Worker and wire encoder |
| Color/symbol behavior | Verified channel swap and empty-high/direction-zero graph | Native encoder and private profile |
| Factory startup | Exact nav/HMI configuration paths and XML process contracts | `prepare_persistent.TARGETS` and transactions |
| Factory ABI | Nav `TWeakPtr`, HMI `std::weak_ptr`; required SomeIP accessors | Hook and live HMI export preflight |
| HMI preload | Exact three-library graphics preload | Startup gate |

Changing `--head` does **not** port the app: the resident addresses, service/model constants, hook destination and profile remain unchanged. Even matching firmware text is not a substitute for matching configuration/executable bytes, dependency exports and actual display behavior.

## Evidence required for a new vehicle

1. Obtain owner authorization, identify vehicle/firmware/HUD hardware, and establish normal navigation/radio operation and a known normal head-unit restart/recovery method.
2. Read and retain original startup files, factory executables, relevant runtime/dependency libraries, network/interface state and identity. Use that vehicle's originals for its rollback kit. Do not reuse another owner's original configuration images.
3. Compare every contract above. Review both factory adapter ABIs and graphics preload. A hash mismatch is a compatibility investigation, not permission to replace expected hashes until the check passes.
4. Verify the RPM source read-only and compare plausible idle values with the factory gauge. Verify actual cluster guidance/list traffic and successful idle/active commit formats. Do not infer idle from silence.
5. Establish a target-appropriate profile and cleanup proof. The current profile builder accepts one particular captured static symbol-free trace layout; it is not a universal profile generator. A known profile may be considered only after the target contracts are established, and still needs that vehicle's bounded drawing/removal validation.
6. Build/audit against that target, run offline regressions, then perform the full [persistent installation acceptance](PERSISTENT-INSTALL.md). Save visual observations and machine evidence separately.

If a contract differs, port and review the relevant code offline before live installation. Keep the existing supported target working; do not relax unknown-state admission, ACK matching, resource ownership or exact-image rollback to make a different target pass.

## Distribution and missing inputs

The tested kit is private and includes proprietary factory bytes. Do not publish it as a universal release. QNX ARM SDK access is supplied separately; the build does not provide licensing or activation. Original project source currently has no public license grant; the scoped `vendor/nbt` extract has its own noncommercial terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Documentation for reuse does not settle redistribution rights.

The earlier DSI adapter investigation is preserved in [historical compatibility notes](docs/history/COMPATIBILITY-RESEARCH.md). Its absent registry service does not block the now-working Ethernet guidance renderer.
