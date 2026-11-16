# Compatibility review — current state

Target: QNX 6.5 ARM little-endian on the Supra NBT Evo OMAP head unit, firmware NBTevo_T24081I. The exact runtime captures and ELF reports are maintained in the private Drive bundle, outside this source repository.

| Area | Offline evidence | Remaining verification |
| --- | --- | --- |
| Toolchain | GCC 4.4.2 ARMv7 builds the observer, replay and self-test; fresh-container build works | Execute the resulting binaries on OMAP |
| Binary format | ELF32 ARM EABI5, little-endian; interpreter `/usr/lib/ldqnx.so.2` | Confirm loader path in the next authenticated session |
| Linked dependencies | Candidate DT_NEEDED closure and strong imported names resolve against captured libraries | Actual target loader symbol selection/runtime behavior |
| Symbol versions | Previous captured runtime version audit resolved 59 requirements; candidates have no GNU version requirements | Loader execution remains the decisive check |
| DSI lookup | All ten required dynamic symbols present; exported client vtable 40 bytes (8-byte header plus eight ARM slots) | Private callbacks, constructor/subobject and thread lifetime at runtime |
| DSI offsets | Prior disassembly corroborates party IDs +0x110/+0x118, channel +0x130, TCP +0x138, IPC fd +0x140; selected callback offsets and payload layout reviewed | Not a complete proof of all private ABI paths |
| HUD protocol | Scoped upstream encoder and pure host tests; registry observation tool ready | Actual Supra 0x82/0 host, owned handles, dimensions, colors, acknowledgements and release semantics |
| Timing | Measured synthetic sequence: 40 calls, minimum 1.95 seconds | Fast enough verified strategy for 300 ms data freshness; current slow sequence cannot be enabled as live tach |
| Telemetry | Prior RPM corroboration; freshness/order/rollback checks tested | Live source integration, shift calibration, optional boost validation |

Vendored adapter changes retain the upstream license and notices. They reject non-32-bit hosts, copy only eight client vtable slots, reject callbacks for unknown clients, align outgoing stream storage, and reject incompatible/error/oversized IPC payloads. The observer keeps callback objects alive until process exit because the upstream API provides no reviewed stop/join contract. Process exit is not proof of remote object cleanup.

The original prebuilt HUD worker contains a gateway-specific assumption incompatible with the observed Supra connection. It is not deployed as a substitute. Center-display LayerManager dimensions are not treated as windshield-HUD geometry. No automatic-transmission EGS source is used for this manual car.

Static checks can be reproduced with `tools/audit_target.py` and `tools/audit_dsi.py` using the separately retained runtime files. They never load the captured libraries. Neither tool is a deployment approval.
