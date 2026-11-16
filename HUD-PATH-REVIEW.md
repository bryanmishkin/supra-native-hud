# Supra HUD path review — 16 November 2026

## Conclusion
The leading transport candidate is Ethernet/SOME-IP to the instrument cluster. The exact windshield drawing surface and safe ownership model remain unproven. Do not enable the legacy MOST sender or reuse the factory navigation instance for a tachometer.

## Evidence and its limits
- Actual car: baseline, radio and navigation windows returned a 112-entry MOST registry without block 0x82 instance 0. This rules out the current observer's assumed host in those windows; it does not prove every MOST path absent.
- Actual car: navigation connection snapshot has established TCP connections from 160.48.199.119 to 160.48.199.96:30502, plus 30501/30503 and another peer at .97. The snapshot is system-wide: it does not assign every socket to a process or identify service IDs.
- Actual car: NavNBTEvoController process memory listing includes a someip library. Its captured binary contains both Ethernet cluster selection and MOST HUD terminal families, plus command-displayable/compression and IC/HUD selection strings. Presence in firmware is not proof of selected runtime behavior.
- Private evidence: NavNBTEvoController SHA256 71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a. No .symtab. The separate private string index records 38 relevant strings with file/virtual addresses and aligned absolute pointer occurrences; it does not resolve ARM PC-relative code paths.
- Reference source: Sq00ky/Supra-iDrive6-Android-Auto commit 87fd9624f33f7ec02d812ebec02a416a3875a320, milestone-7/src/cluster/j29_client.hpp, j29_graph.hpp and readme.md. It describes service 0xB006 on TCP 160.48.199.96:30502 and route-guidance model updates. This is reference-car evidence, not a capture of this Supra's service.
- Reference code explicitly avoids create/dispose and patches a factory-owned navigation graph (default handle 0xC8). That demonstrates a navigation integration approach, not arbitrary independently owned tachometer drawing. We have not imported its sender.
- The broad MOST capture retained headers, lengths and counts, not payload bytes. It cannot retrospectively reveal Ethernet service IDs, graph bodies, shape coordinates, or ownership.

## App work
The native core, synthetic renderer and fail-closed session remain available. Production 300 ms freshness remains unchanged. The old 40-command sequence at minimum 50 ms intervals takes at least 1950 ms and cannot meet that budget. Selecting Ethernet alone does not fix this; a supported atomic/batched update and measured latency are needed.

Added tools/inspect_someip_stream.py: local-only, bounded 16 MiB inventory of a gap-free reassembled TCP direction starting on a message boundary. It validates lengths and protocol, rejects truncation instead of guessing, and reports service/method/type counts without payload disclosure. It does not read PCAP directly, reassemble TCP, transmit, or authorize drawing. Five tests cover coalesced frames, all truncation points, bad lengths/protocol, size limits and no resynchronization. Existing QNX binaries remain unchanged; this Python analysis tool runs on the Mac.

## Next car session: prerequisites and ordered captures
1. Inventory available passive capture facilities and identify the internal VLAN/interface. Do not assume tcpdump is installed or that the Mac's diagnostic ENET link sees internal VLAN traffic. If no suitable passive facility exists, stop and choose a separately reviewed capture method; do not redirect traffic or change routing automatically.
2. With a bounded duration/file limit, collect internal cluster traffic in separate normal/radio/navigation windows, recording exact times and visible windshield state. Capture both directions and packet payloads privately. Radio Mode presses must be recorded as a confounder.
3. Offline, reassemble each TCP connection direction with sequence/gap/retransmission validation. Export message-aligned streams to the new inspector; preserve originals. Confirm service IDs, request/reply correlation and methods before interpreting model bodies.
4. Resolve the runtime cluster selection, IC versus HUD display destination, drawing/command versus navigation model service, ownership/allocation/release behavior, overlay arbitration and independent surface availability. Do not assume 0xC8 is free or stable on this car.
5. Only after that evidence supports a separate surface, implement the transport adapter and review a parked minimal draw/erase test with verified cleanup. No live drawing test is prepared yet.

No extra car session is needed to establish that the QNX build executes: all 10 target self-tests and the synthetic 40-call replay already passed. The missing evidence concerns transport, display ownership, latency and real telemetry semantics.
