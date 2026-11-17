> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

> Later trace, 16 Nov 2026: [SESSION-CONTRACT.md](SESSION-CONTRACT.md) resolves the factory sink state machine (selection 0 = HUD, 1 = Kombi), create structure/configuration response, initialize method 4, dispose method 7 and resource-dispose method 8. The earlier uncertainties below are historical; independent surface ownership and remote lifetime remain unproven.

# DisplaySink and guidance creation — offline review

16 November 2026. Car disconnected. No vehicle/network commands were issued.

## What the configuration and captures establish
The double-read `/etc/someip/services.conf` maps instance 1 of RICServiceGuidance to B006, RICServiceList to B00E, and DisplaySink to B009. These are BMW.Kombi interfaces. The watched navigation capture contains B009 traffic with cluster 160.48.199.96:30503; the guidance/list model traffic previously appeared on port 30502. The temporary loopback instance-42 entries in someip.conf are not the observed cluster endpoints.

The B009 generated client implements display-switch notification and completion. It is not an identified arbitrary shape/surface allocator. Guidance has a separate `ric_create` method. No B006 create request/reply was present in the saved windows. The earlier MOST shape renderer remains a separate, not-proven-active path.

## Static trace
Addresses below are in NavNBTEvoController SHA256 71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a. Local evidence includes disassembly and ELF-resolved import names.

| Operation | Evidence |
| --- | --- |
| Switch completion | Function 0xbd15b4 logs requestSinkSwitchCompleted. At 0xbd16c0 it sets method 1; at 0xbd16cc it sets message type 1 (request without response). Serializer 0xbd1578 calls the one-byte serializer 0xba3588 twice. |
| Switch event | Dispatcher 0xbd19c0 reads event ID and compares 0x8001, then calls 0xbd18ec, which logs handleEventRequestSinkSwitch. |
| Event layout | 0xbd1890 calls 0xbd1818 (8 bytes, endian conversion), 0xbcc138 (fixed array of exactly two elements), and 0xbc1280 (one byte). Array element reader 0xbc80a0 consumes two bytes and swaps byte order. Total body is 13 bytes. |
| Event delivery | 0xbd18ec passes the decoded three fields through virtual slot +0x14. Concrete logged handler 0x2c4e98 converts the array and forwards via object+0x74, virtual slot +0x24. This does not establish a windshield destination or an allocation permission. |
| Guidance create | Function 0xba41c8 logs requestRic_create. It passes method 1 to header helper 0xba0864, which calls setMethodID and sets message type 0 (request). It serializes a structured argument through 0xba41c4/0xba4120/0xba4090, not an empty allocation command. The full structure and permitted clients remain unresolved. |
| Create response | Logged responseRic_create handler 0x2c0b8c converts returned data and forwards via object+0x74, virtual slot +0x7c. A static response implementation is not evidence that another client can successfully allocate a surface. |

ELF imports confirm setMethodID at 0x12875c, setMessageType at 0x12a55c, setSessionID at 0x12a718, read at 0x12a04c, write at 0x12a604 and getEventID at 0x1273c4. Literal-pool decoding and unproven runtime selection remain limitations of static disassembly.

## Actual saved B009 messages
Exactly two B009 messages were found across all five reassembled capture windows, both in navigation-watched:

- Cluster to head unit: event 0x8001, type 2, interface 1, return code 0. First eight raw bytes `3ff0000000000000`; two big-endian 16-bit values 460 and 237; final byte 1.
- Head unit to cluster: method 1, type 1, interface 1, return code 0; two raw completion bytes 1 and 0.

These are separate TCP directions. This review does not infer cross-direction ordering from stream enumeration. The pair 460/237 is not labeled as width/height; the first field is kept as raw bits rather than assigned floating-point, timestamp or priority semantics. The completion bytes are not labeled success or a destination enum. None is a surface handle or authorization token established by this evidence.

## Code and validation
Added allocation-free C++98 passive DisplaySink decoding to the existing model module and offline inspector. It accepts only B009/interface 1/return code 0 with event 0x8001/type 2/exactly 13 bytes, or method 1/type 1/exactly 2 bytes. All other combinations fail closed and reset output. Raw fields are preserved. No sender, allocator or ownership flag is enabled.

51 host/Python tests pass. New tests cover endian-distinct synthetic fields, completion fields, malformed lengths, wrong service/method/type/version/return code and no drawing authorization. All saved message-aligned streams passed the updated inspector, and both actual B009 messages decoded. The existing QNX SDP 6.5 ARM build succeeded, including the updated decoder object. This is a build check, not execution of the new decoder on the vehicle.

## Route toward an independent tachometer surface
1. Continue tracing the structured guidance create argument and response into their callers and cluster-facing object lifecycle; identify whether it creates a model service or a drawable region.
2. Resolve the meaning of DisplaySink's fields and its upper-level consumer. A sink-switch exchange alone does not establish independently composited pixels.
3. Establish a distinct allocation accepted for our client, windshield destination, supported content/geometry, overlay priority, lifetime/release and bounded update timing. Factory handles 100/200 are not ours.
4. If static analysis cannot establish the initial exchange, prepare a passive capture spanning factory RIC initialization. No reboot, navigation action or new car session is requested now, and no create/switch packets should be guessed or transmitted.

Current app core and rendering encoder remain usable offline. Production live drawing remains blocked on the allocation/content contract; generated interfaces and successful factory traffic do not remove that gap.
