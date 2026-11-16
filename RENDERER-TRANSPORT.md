# Renderer transport and Ethernet applicability

Offline review, 16 November 2026. No vehicle connection or commands were performed.

## Conclusion
The concrete CIcHudComm_TF11_13 shape renderer traced from DNAVIManeuverView feeds a logical MOST command packetizer. It is not an identified B006 SOME/IP drawing backend. Combined with the Ethernet coding branch that skips MOST guidance initialization, this weighs against treating this renderer as active on the Supra. Static evidence does not prove which instance runs, nor exclude a downstream bridge. An independently owned windshield surface remains unproven.

## Trace evidence
Addresses refer to the previously hashed captured NavNBTEvoController unless named otherwise.

- Constructor 0x77c590 stores vptr 0xfafad8; slot +0x38 resolves callback 0x77ce68.
- Polyline helper 0x77b390 calls 0x777f5c at 0x77b4a0. That packs arguments and queues through 0x771b6c/0x771b58, whose callback is 0x7744f0.
- Callback 0x7744f0 invokes 0x9418dc, which logs HUDTerminal.ImageAddPolygonCall and imports addSession, sendAck and sendPacketizerFlush.
- Definitions are in captured libimp_sys_most_base_nbt.cpp-ne.so.17: sendAck at 0xeb6a4 (832 bytes), sendPacketizerFlush at 0xd837c (248 bytes).
- sendAck checks HBMOSTTypes method/op-type and session state, serializes CHBByteStream and dispatches through an interface. Flush builds DSYSMOSTTypes::MessageType, obtains logical-device/function fields, copies the byte stream and dispatches virtually. The downstream physical transport has not been fully resolved.
- The mangled suffix in sendAckEth encodes C++ argument types; it is not evidence of Ethernet.
- Constructor field +0x4c receives 0x81. Its semantic meaning is unresolved. As a conservative cross-check, all saved baseline/radio/navigation registry snapshots were searched for blocks 0x81 and 0x82 (key high byte); neither appears. That absence alone does not establish the constructor field's meaning or rule out other interfaces.

PC-relative literal annotations in shared-library PIC code must not be treated as absolute string references without resolving relocation/base arithmetic. Disassembly may decode literal pools as instructions. Symbol attribution above uses ELF imports/definitions, not coincidental strings.

## What is needed for our own surface
Resolve the active ManeuverView.DNAVIManeuverView provider, its Ethernet branch and the session-to-cluster-object binding. Establish a distinct client allocation, windshield destination, overlay priority, bounded update timing, and release behavior. Factory handles 100/200 and existing navigation sessions are not app-owned surfaces. The existing model decoder and fail-closed drawing core remain useful; no speculative live sender is enabled.

## Prepared next capture
`python3 tools/collect_surface_bindings.py` prints a local plan without network access. Explicit `--execute` requires verified head/local addresses, a known-hosts file and a new output directory; optional socket reuses an existing authenticated connection. It verifies direct QNX hu-omap ARM identity, then double-reads only:

- /opt/nav/eceusa/bin/navigation.ini
- /mnt/share/nav/NavCtrl_DB.ini
- /etc/someip/someip.conf

Paths are grounded in saved process arguments. Each read is capped at 1 MiB plus one block to detect oversize, with a 30-second timeout. Only matching, successful reads are saved with hashes. Missing, oversized or unstable files are reported. This reads configuration only; no remote writes, service changes or activation. Configurations are private evidence and must not enter the source repository. The tool has not run on the car. These files may identify the provider; their contents are not yet known and success is not guaranteed. Inspect them before selecting any additional provider files or initialization capture.

## Validation
47 host/Python tests passed, including default no-network behavior, exact double-read capture, wrong-host rejection and unstable-file rejection. No C++ runtime changes were made in this review. Existing successful QNX builds remain the baseline; this change adds a host-side capture tool and evidence documentation only.
