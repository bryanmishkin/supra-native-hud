> Completed on19November: [actual response and verification](RECEIVER-IDENTITY-RESULT-2026-11-19.md). This preparation document is retained for reproducibility; the missing identity is no longer a reason for another trip.

# Exact next receiver measurement

19 November 2026. Offline work reached a missing **target identity**, not a demonstrated root-canvas API. Keep installed V1 unchanged. No Hz tests and no speculative root-memory writes.

## What was exhausted in the retained evidence

- Seven saved diagnostic queries identify gateway10, DME12 and head unit63. Four positive F101 responses (including the duplicate direct/gateway HU read) decode consistently. None identifies the cluster.
- B001/8004 in the selected retained TCP sessions has five distinct 36-byte bodies containing cellular operator text, originating from `.97`, not the drawing endpoint `.96`. It is not receiver firmware identity or canvas geometry. Raw network/operator payloads remain private.
- An ELF-header inventory of extracted `outputs/` files found 1,500 ELF files including duplicates: 1,490 ARM and ten x86-64. No MIPS ELF was found. This rules out an extracted BO03 MIPS ELF in that inspected set, **not** a different ARM receiver implementation, compressed firmware, or raw non-ELF firmware. The files are not relabeled matching receiver code based on architecture alone.
- The B006 advertisement bounds bitmap resources to150×36 and PiP resources to320×320. B00E advertises128×128 bitmap resources. These do not identify the root scanout or guarantee visible area.

The receiver cannot be matched to a firmware build from these records. The next required measurement is its own system name and HWEL/BTLD/SWFL/SWFK inventory. A matching inventory is necessary for firmware selection; it does not by itself obtain firmware or establish an external drawing API.

## Prepared capture

`tools/capture_receiver_identity.py` uses the project's previously used HSFZ framing and only UDS ReadDataByIdentifier requests:

| Target | Request | Purpose |
|---|---|---|
| Gateway10 | `22 3F 07` | Retain configured-ECU list, if supported |
| Explicit candidate | `22 F1 97` | Returned system name |
| Same candidate | `22 F1 87` | Manufacturer part number |
| Same candidate | `22 F1 89` | Software version |
| Same candidate | `22 F1 01` | Full software inventory |

The configured-list DID is cross-checked against [Hadi Cherkaoui's klartext source at c711b200](https://github.com/HadiCherkaoui/klartext/blob/c711b2003aa8e1dafc2cfa7cc143840dee72d416/crates/client/src/client.rs). That source marks the response layout as derived and unverified on a car. Our capture therefore saves it raw and does not use a speculative decoder to choose an ECU. No upstream code was incorporated or executed.

[packetpilot's F-series table](https://github.com/packetpilot/bmw-f/blob/master/readme.md) lists KOMBI at60. This is a **candidate address**, not a Supra identity match. Require the returned name and inventory before associating its software with the cluster. An unexpected name, unsupported DID or timeout remains evidence and must not trigger blind address scanning or a reset.

Offline plan (no sockets):

```sh
python3 tools/capture_receiver_identity.py --ecu 60
```

When connected, first read the Mac's actual adapter/source address and gateway route. Then, using those verified values:

```sh
python3 tools/capture_receiver_identity.py --execute \
  --gateway "$VERIFIED_GATEWAY_IP" --source-ip "$VERIFIED_MAC_IP" \
  --interface "$VERIFIED_ENET_INTERFACE" --ecu 60 \
  --output "$NEW_PRIVATE_IDENTITY_CAPTURE"
```

Five requests only; each has a bounded response deadline and each result is saved separately before the next begins. No SSH dependency, V1 pause, iDrive reset, session switch, security access, writing, coding or programming. An awake diagnostic network is required; this identity read does not need a visible HUD or engine revving. Do not move the vehicle for it.

## Same-session decision and existing larger-image cases

Review the raw positive identity response immediately. Match returned hardware and software identifiers/versions to candidate receiver code; do not select the BO03 reference simply because it has a HUD emulator. Save negative responses too. If identity does not establish the receiver, stop identification guessing and preserve the evidence.

The [canvas batch](NEXT-CANVAS-SESSION.md) is already executable for corrected Carousel content fields and Entertainment content columns, with36/64/96/128 images and exact restoration. These can measure larger **widget** areas in the same parked session if desired and admitted; they are not prerequisites to the identity read and cannot prove the root canvas. No repeat control or Hz test is mandatory.

**Main-root test admission remains unmet:** no matched receiver implementation, root dimensions, externally reachable pixel-binding contract or root-image cleanup contract. Do not schedule a purported main-canvas drawing attempt until those exist. This is the precise boundary requiring new vehicle evidence, rather than another selector update.

## Offline validation

The F101 parser was replayed against all four retained positive responses and matched every saved ID/version and entry count. It rejects unknown header versions and count/length mismatches while capture retains raw data. Tests cover malformed/truncated responses, unknown class preservation and the fixed read-DID allowlist. Live transport and the cluster's response remain untested; passing parser tests does not claim otherwise.
