# Cluster source and documentation review

16 November 2026. Offline only. This review does not establish a live drawing test.

## New result: the apparent local server is a forwarding adapter

A signature audit of 54 unique saved ELF files and three unique configuration files found `RICServiceGuidanceStubTs` inside NavNBTEvoController. That is a useful lead, but tracing it resolves the apparent server back to the outgoing client:

1. Stub constructor `0xb9a204` is called at `0x2b3a80` by adapter constructor `0x2b3a74`.
2. The adapter installs vtable `0xec7f08`.
3. Stub create dispatch `0xb9a3b4` selects virtual slot `+0x24`, whose value is `0x2bb770`.
4. That implementation converts the local arguments and, at `0x2bb7b4`, calls `0xba41c8`, the already traced outgoing SOME/IP create request.

This is a local MoCCA-to-SOME/IP bridge, not the cluster allocation implementation. Its adjacent registration string names `CSomeIPClient_SomeIPRIC_IKE3D_RICServiceGuidance`. The evidence applies to controller SHA256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`. Private region traces and the hashed inventory are in the Drive evidence archive.

The same audit found no searched DCSM2 or RAMSES signatures. That is a bounded negative result over the retained files, not proof of absence from the whole vehicle or from stripped/compressed code. `tools/renderer_evidence.py` makes this distinction explicit and avoids the false match between `Ramses` and `getParamSession`.

## Public implementations checked

| Source | Useful finding | Applicability |
|---|---|---|
| [cluster-render DCSM2 documentation](https://github.com/robertnisipeanu/idrive-apps/blob/c861d710a8a2d0686058ea35798bdb88193a4ee3/native/cluster-render/dcsm/DCSM.md) | Describes independent client IDs, fetch/map/unmap/unfetch, status events and a per-client watchdog. | iDrive 7 service B05F with RAMSES. These contracts cannot be assigned to Supra B006. |
| [cluster-render implementation](https://github.com/robertnisipeanu/idrive-apps/blob/c861d710a8a2d0686058ea35798bdb88193a4ee3/native/cluster-render/src/unit_idrive7.cpp) | Connects a RAMSES participant and DCSM2 client, releases targets at shutdown. | Linux/MGU implementation, not a QNX NBT Evo drop-in. No third-party source was copied into our app. |
| [HUD Widgets](https://github.com/nhocleopro/hud-widgets/blob/e9c3e695f2c18f2f2e03eecddd661144da38eb5b/README.md) | A tachometer app using cluster-render. | Its successful HUD reports concern iDrive 7; appearance is not protocol compatibility. |
| [NBT CarPlay KOMBI stack](https://github.com/ftojke/BMW-iDrive6-CarPlay-HUD/blob/97b91338789a93c3638f1895ddc2ed5ee5f194f9/hook/kombi/README.md) | Reuses the NBT-AAD navigation graph/client. | Another factory navigation route, not a new independent drawing allocator. |
| [EntryNav RIC recorder](https://github.com/CallMeLewis/AA-EntryNav/blob/c89b1ecaaf7d087f1bb44b6c4db3948d0e73774f/tools/evo_ric.cpp) | Names RIC interface and local MOST service RbRicService. | Passive recorder, not the Ethernet cluster server. |
| [KombiKraft firmware setup](https://github.com/callan280/kombikraft/blob/22f66e1130ce85774abc89bb3ea0ff1745ec50e6/docs/firmware-setup.md) | Explains matching SWFL/BTLD/HWEL identification and full programming-data extraction. | No matching Supra firmware or ready cluster server is distributed. F40/F97 material is not a Supra profile. |
| [IDEmu cluster/HUD scope](https://github.com/herrbimmer/IDEmu/blob/753faebe17c739d6804e680b8affe653373b24e3/docs/CLUSTER_HUD.md) | Explicitly distinguishes its simulated drawing from the vehicle's cluster renderer. | Its browser HUD is not evidence that original Supra server code executes offline. |

Exact RIC interface/stub searches produced no matching public server implementation or interface-definition file in the returned results. Search indexing is incomplete; this is not a claim that none exists anywhere. Search results referencing this project's own earlier notes were excluded as independent evidence.

## Firmware acquisition boundary

The saved decoded software inventory contains ECU addresses 10, 12 and 63, with duplicate head-unit entries. It does not identify a cluster firmware record. The head-unit SWFL list must not be labeled cluster firmware. Searches of the available Drive files and local Downloads/Codex file names did not locate a full PSdZData set or a matching cluster image.

The useful acquisition target is therefore a matching cluster application image plus its HWEL/BTLD/SWFL identification, or the RIC/B006 server interface and allocation documentation. A dealer/programming inventory already saved elsewhere could supply identification without another vehicle session. This review does not request a new capture visit or recommend flashing firmware.

## What can and cannot be tested

The new scanner and existing lifecycle/configuration decoders run offline. Their tests verify classification, byte formats and rejection behavior. They are not a simulated substitute for cluster acceptance or a windshield drawing test.

The actual marker test remains unimplemented: creating a client, inventing a resource range and transmitting a bitmap would still guess the server contract. Porting the MGU sender would transmit the wrong protocol. Reusing the known factory navigation handle would change the ownership premise rather than solve it. The newly traced forwarding stub closes a real lead but does not supply that missing implementation.

No executable from these third-party projects was installed or run. No vehicle connection, drawing transmission, persistent hook or coding change occurred.
