# Independent surface investigation — 16 November 2026

## Current answer
An independent windshield drawing surface has not been established. The strongest new result is a trace separating the internal displayable-session API from local C++ allocation and from cluster SOME/IP traffic. Calling an internal registration routine or choosing an unused numeric handle is not a demonstrated way to obtain a surface.

## Factory binary trace
All addresses below refer only to the captured NavNBTEvoController SHA256 71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a. Disassembly and reproducer scripts are private Drive evidence, not code to execute against the vehicle.

1. Ethernet selection: getter 0x6f453c reads internal lookup argument 0x48800818, labels value 3 KOMBI_CIC_kombi_ethernet and returns that value. At 0x6ddbac the caller invokes that getter; comparison against 3 at 0x6ddbb0 takes the path that logs “ethernet IC coded, do not start MOST guiding” and returns at 0x6dde0c. This bypass concerns this MOST guidance initializer, not proof that every MOST feature is absent. No coding change is suggested.
2. Local allocation: 0xa7c91c passes 0x3c to 0x323fc4. That helper rounds to an 8-byte boundary and calls PLT 0x12a034, resolved through .rel.plt to operator new[] (_Znaj). The size and returned pointer describe a local heap object. They are not a cluster surface ID or remote ownership grant.
3. Registration path: 0xa7ce7c constructs registration arguments, calls 0xa7ce50, then links through 0xa7ca68 and 0x6d8d94 to callback 0x6ddb00. That callback reaches 0x311488. Its log identifies userID, type, width, height and a list of options. At 0x3115c8 it calls proxy routine 0xc27428.
4. Proxy boundary: 0xc27428 references DNAVIManeuverView. Its imported calls resolve to CHBProxyBase::isRequestPossible, addListener, CHBRegisterProxyBase::setRegistryNotification and CHBProxyBase::sendRequestEvent. This proves a framework request boundary. The local constants 4, 0x14 and 0x80000003 seen there must not be promoted to external SOME/IP service/method identifiers.
5. Asynchronous result: 0xa7c7c4 compares the returned request object with the pending object at +0x54 before accepting result fields. It stores two returned values at +0x18/+0x1c, sets a completion flag at +0x50 and logs a displayable session/user ID. Stop path 0xa7c98c initiates unregister handling and clears the saved values to -1. Adjacent logs distinguish displayable and MoCCA session IDs. Their relationship to external factory handles 0x64/0xC8 is unresolved.

These observations identify an internal lifecycle contract worth tracing, but do not prove that another application may register, that this route is active on this Supra's Ethernet HUD, or that a registered displayable can draw arbitrary tachometer primitives. The same binary contains multiple vehicle variants and display paths.

## Captured traffic cross-check
The new offline audit preserves both TCP endpoints and service/method/client/session/interface identifiers. All 57 radio and seven navigation request/reply pairs match within their own connection and have protocol-level success replies. No method-1 request appears for either target service during these windows. Method 1 would still need interpretation if captured; its presence alone would not prove independent allocation.

The audit labels observed first-word handle prefixes as factory-used evidence, separates handles by service and connection, flags duplicate transaction identifiers as ambiguous, and reports missing/rejected replies. It never produces drawing permission. This avoids accidentally pairing a reply from another connection or treating an accepted factory update as a successful app allocation.

Run locally:

```sh
python3 tools/audit_model_sessions.py /path/to/reassembled-window
```

Input is an inventory.json and stream files from extract_someip_pcap.py. All 39 Python/host tests pass, including endpoint separation, ambiguous IDs, missing replies, rejection, and unknown allocation semantics. No vehicle access or new live sender was added in this investigation.

## What would establish a usable independent surface
The missing contract must tie together: the active provider of DNAVIManeuverView; permitted registration type/options and client identity; returned displayable/MoCCA session values; routing to the physical windshield; creation and release of distinct cluster-side objects; overlay arbitration; and update/cleanup timing. A registration result must be demonstrably distinct from factory-owned state. A client ID alone is insufficient.

Next useful static targets are the provider/binding configuration for ManeuverView.DNAVIManeuverView and the implementation that translates its displayable sessions to Ethernet cluster objects. Their mapping is not established by the current captured libraries. If static analysis cannot recover that mapping, a later passive initialization capture with known visual state would be necessary. Do not restart factory processes, change coding, send guessed allocation requests, or claim an independent surface is ready.

The existing HUD geometry/core and observed-model decoder remain usable offline. An independent live drawing adapter cannot yet be implemented faithfully; fabricating that contract would not advance the app.
