> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# Actual-car model decoding — 16 November 2026

## Findings
The captured Supra sends structured model requests over SOME/IP, not the old MOST line/circle command stream. Navigation uses service 0xB006 with request-body handle 0xC8; radio interaction uses 0xB00E with handle 0x64. These are factory-used handles observed in this session, not app-owned handles or guarantees of stability across boots.

The watched navigation start contains seven matched request/reply pairs: method 0x09 three times, 0x02 twice, 0x03 once, 0x0E once. All SOME/IP response codes are zero. Both method-0x02 replies carry a one-byte value 01; its full semantics have not been established. Navigation updates expose model types 0x11, 0x21, 0x03 and 0x28.

Comparison with Sq00ky/Supra-iDrive6-Android-Auto at commit 87fd9624f33f7ec02d812ebec02a416a3875a320, milestone-7/src/cluster/j29_graph_template.hpp, finds four of the seven request bodies byte-identical to stored template bodies: one 0x09 state-like update, two 0x02 references and one 0x0E update. The other bodies have matching model identity/type/tag prefixes and variable content. This is body comparison, not independent proof of every reference project's semantic label. The template and accompanying j29_graph.hpp identify navigation text and guidance models; they do not expose an independent arbitrary-shape surface. Captured road text is private and excluded from source/tests.

Radio contains exactly 19 ordered cycles of methods 0x0B, 0x09, 0x04, with 57 matched responses and zero response codes. Each 0x0B body is 94 bytes: observed model ID 0x6D, type 0x1C, tag 8. Its payload contains a candidate 64-byte block consisting of four 16-byte records. Five distinct record orders appear across the 19 updates. Each 0x09 body is 26 bytes with model ID 0x65, type 0x2E, tag 3, and a trailing word 0x6D. Each 0x04 body contains only handle 0x64. A list-update interpretation fits the radio interaction; naming fields as coordinates or method 0x04 as an atomic display commit would exceed the evidence.

## Shared update envelope observed

| Body offset | Bytes | Decoded field |
| --- | --- | --- |
| 0 | 4 | Big-endian factory-used handle |
| 4 | 4 | Model identifier |
| 8 | 1 | Model type |
| 9 | 4 | Payload length, equal to body size minus 17 |
| 13 | 4 | Tag/version-like value; role not proven |
| 17 | variable | Payload beginning with repeated 4-byte model ID and 1-byte type |

The 9-byte navigation method-0x02 body is a model reference layout; the 4-byte radio method-0x04 body is handle-only. Neither is forced into the update envelope.

## App changes and validation
Added C++98 src/someip_model.hpp/.cpp: a bounded, allocation-free decoder for the observed service/method/type combinations. It validates lengths and repeated identity/type fields, resets results on failure, and rejects unknown combinations. It records values rather than hardcoding handle 0x64 or 0xC8 as owned. Payload details beyond this envelope remain undecoded. No networking, encoder, sender or allocation command was added.

Added tools/hud_model_inspect.cpp: an offline, message-aligned stream reader that only decodes request messages, reports metadata without payload text, and always reports drawing_authorized=false. It rejects invalid protocol, truncated framing and oversize messages. It can emit earlier complete records before a later framing error; consumers must check its exit status.

Compile on the Mac:

```sh
c++ -std=c++98 -Wall -Wextra -Werror -Isrc src/someip_model.cpp tools/hud_model_inspect.cpp -o hud-model-inspect
./hud-model-inspect < reassembled-stream.bin
```

All 64 target-service requests from the private captures decode successfully. Host C++ envelope tests and all 33 Python/host tests pass. The decoder object builds with QNX 6.5 ARMv7 GCC 4.4.2; it has not been run on the car. Synthetic test data contains no OEM payload or route names. Existing live-drawing gates and 300 ms production freshness limit remain unchanged.

## Binary review and remaining boundary
The two newly captured SOME/IP libraries expose generic protocol, service configuration and command-dispatch machinery. The MoCCA bridge imports CServiceConfigurationManager::loadConf. This identifies configuration loading as another trace point; exported names alone do not resolve the HUD object schema or display destination. Previous navigation-binary selector and command-displayable registration anchors remain relevant.

Next offline work can correlate model bodies, template semantics and factory code paths. Missing evidence is the allocation/lifetime and routing of an independent drawing surface, plus safe overlay arbitration and timing. The current capture begins after existing sessions were established; it does not contain their initial creation/ownership handshake. Do not overwrite factory objects or substitute a modified navigation graph as a tachometer. If static analysis cannot establish that contract, a future targeted passive initialization capture will be needed; no additional session is being requested now.
