# Receiver binding: available evidence and hard limit

No larger-windshield fix is ready. This review makes no runtime or selector changes, and does not authorize another marker attempt. V1, its baseline tag and installed files remain unchanged.

## Upstream check

Rechecked ryseek's public branches and [draft PR 232](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/pull/232) on 18 November 2026. The G30 branch and PR head are still `a0242e1c30d17b138845c18d6bf86ae0cd99ead6`; the other listed branch is main. No separate published HUD implementation was found in that branch listing.

The PR describes instrument-cluster video and lists incompatibility with enabled HUD. Its prose about software decoding is older than the head commit, so use source for current decoder details. The source's `native/control.hpp` explicitly pauses cluster output for HUD selection, and `profiles/g30.hpp` defines that alternate destination. Neither implements custom video in the windshield.

[Ryseek's routing report](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/issues/226#issuecomment-6926997386) says the video travels from head unit through cluster to HUD and needs additional routing setup. This is a report from the reference vehicle, not a decoded Supra receiver contract. Credit ryseek for this lead; do not present it as our discovery or as proof of Supra compatibility.

## What is missing

The unresolved operation is the receiver's association of the incoming native pixel stream and metadata maneuver identity with a selected windshield image. We have not identified the receiver function that performs that association, its state prerequisites, or its forwarding configuration.

The available analyzed binaries (`NavNBTEvoController`, `NavigationFully`, `HmiMain3D`, Screen/WFD drivers) execute on the head unit. Their session/job setters and selector predicates do not execute the cluster receiver. Local Screen posts, matching metadata, Guidance acknowledgments and B009 completion do not demonstrate that association.

The public bimmulator firmware helper identifies Bosch BO03 6WB program `00003e5b`, config `00003e5c` and graphics `00003e5d`, version `007_003_005`. That is not an established identity match for this Supra. Do not label those images the target receiver, download an arbitrary replacement and infer compatibility, or flash them. The owner previously reported no saved programming-data set or ECU inventory.

An offline resolution needs at least one relevant primary artifact: the matching receiver implementation with provenance, a documented native-stream/HUD routing contract, or a published working windshield implementation with its complete startup and removal sequence. None has been established by this review. A larger image cannot be promised from the existing HU-only execution tests.

## Consequence for engineering work

- Keep the failed live runner retired. Do not revive it merely by wiring the tested B009 codec into a socket.
- Preserve the offline codec/replay: it closes a protocol-encoding gap, not the receiver-binding gap.
- Do not add more HU selector tests as a substitute for tracing the missing receiving function.
- Do not ask for a car trip to repeat the same arrow-only candidate.
- Once a relevant artifact becomes available, trace stream association, windshield destination and withdrawal together; compare those operations against both failed captures before producing a revised candidate.

This is an evidence limit, not proof the hardware cannot display a larger image. No new application build was warranted by this review. The previously proven 150×36 V1/V2 path remains separate.

## Expanded source search and complete retained-PCAP audit

Follow-up offline search checked indexed receiver/service symbols and additional public implementations rather than adding selector tests:

- `st1ng/nbtevo-carplay-advanced` and `Barlows/nbtevo-carplay-advanced` both resolve to `9a80636b5d8c6eee259105a5e9311b912935a9c7`. The former's `src/kombi.h` explicitly uses the Ethernet navigation graph for G-series/J29, while `src/hud.h` implements the different MOST terminal. This does not provide native windshield pixel routing. ftojke remains at `97b91338789a93c3638f1895ddc2ed5ee5f194f9` with the same navigation-graph approach.
- [MRcoding source description](https://github.com/mrcodingvienna/NBT-Evo-HUD-CarPlay/blob/5ed6c07e28e2da76b572cd4287e0480890d24236/README.md) targets an F30 and describes its HUDTerminal work as incomplete/offline. Its use of “receiver” concerns CarPlay input, not a supplied Supra cluster receiver.
- [JayJay3071's measured 6WB terminal](https://github.com/JayJay3071/nbt-android-auto/blob/12c8411618acd3eea5fb0a5ff1a57ef1c87761e0/docs/CLUSTER-HUDTERMINAL.md) is MOST-based. It also records bitmap acknowledgments without visibility in some surfaces. Neither its surface sizes nor its successful polygon drawing establish Supra Ethernet support.
- The indexed `RICServiceGuidance` hits outside this repository lead to passive capture tools and `MakaveliRoberto/iDrive-6-local-run` head-unit service configuration, not a receiver implementation. Recursive-tree retrieval for that dump and KombiKraft failed with a transport error; do not describe those repositories as fully searched. The dump's root and indexed service files were accessible.
- A public DKOMBI2 ODX base definition in `jill-super/VectorSipPack_BSW_RH850_BMW` at `52da21fd20cf3cc294daf1af20cb9bd47474c16b` is diagnostic XML, not the application image. The inspected file contains no APIX, PiP, video, or pixel contract. It is not an identity match for the installed car.

The offline audit enumerated all **57 `.pcap` files under the saved outputs, 29 unique SHA-256 contents**. Six selection events and six completions were found in four unique recordings; every decoded selection is scale 1, **460×237, selection 1**. None supplies a selection-0 windshield handshake. This is a captured-interval result, not proof no HUD route exists.

One recording failed the full strict audit because of a gap on Guidance port 30502. A separate, offline `tcp port 30503` filter retained 346 packets and decoded without errors or selection events. Another recording has a truncated Guidance message; that error is retained in the inventory. No malformed bytes were repaired or treated as a successful route. The original captures were not changed. Private `all-sink-captures.json` preserves paths, duplicate groups, hashes, events and failures, with the filtered audit alongside it.

No matching receiver code or working native windshield implementation was obtained. The practical external lead is ryseek's reported factory HUD capture. A specific question requesting the stream/metadata/Guidance association, routing setup and withdrawal sequence is prepared privately; it has **not** been posted without owner authorization. No new vehicle session is requested, and the retired runner remains disabled.

See [missing sink contract](PIP-SINK-CONTRACT-GAP-2026-11-18.md), [offline codec/replay](PIP-DISPLAYSINK-IMPLEMENTATION-2026-11-18.md), and [failed revision 2](PIP-REVISION2-RESULT-2026-11-18.md). Private archive retains the fetched upstream evidence; proprietary factory captures remain out of GitHub.
