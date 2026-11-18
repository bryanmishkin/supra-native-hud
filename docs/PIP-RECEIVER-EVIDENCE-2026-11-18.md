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

See [missing sink contract](PIP-SINK-CONTRACT-GAP-2026-11-18.md), [offline codec/replay](PIP-DISPLAYSINK-IMPLEMENTATION-2026-11-18.md), and [failed revision 2](PIP-REVISION2-RESULT-2026-11-18.md). Private archive retains the fetched upstream evidence; proprietary factory captures remain out of GitHub.
