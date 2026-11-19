# Main HUD renderer investigation — 19 November 2026

The target is the **whole windshield rendering system**, including the parent surface beneath navigation/menu widgets and the speed, speed-limit, warning and alignment regions. No arbitrary root drawing interface is established yet. This status distinguishes new evidence from that unresolved outcome.

## Complete retained TCP inventory for the selected HUD sessions

`audit_hud_service_inventory.py` audited saved inventories from the MOST/canvas session, targeted navigation/height session and latest canvas session. Deduplication by stream SHA and directional endpoint tuple yielded **124 unique TCP streams**, zero recorded stream parse errors in these inventories, and service IDs:

| Service | Evidence interpretation |
|---|---|
| B001 | Other captured service traffic; not established as a drawing surface |
| B003 | Retained telemetry includes NMEA; not pixel frames by size/frequency alone |
| B006 | Known guidance model/resource path; 150×36 custom image demonstrated |
| B009 | DisplaySink selection/handshake; receiver pixel association unresolved |
| B00E | Factory widget model/resource path; bitmap-producing content-cell candidates prepared |
| B011 | Check-control asset retrieval in the cluster-to-HU direction |
| FFFF | SOME/IP-related control traffic in retained TCP inventory; not a drawable layer |

This audit uses previously parsed TCP inventories. It is not a full CAN/MOST/UDP inventory and does not rule out unobserved or internal receiver interfaces. It establishes which service families are actually retained before selecting the next reverse-engineering target. Raw paths/endpoints remain private.

## Receiver and producer boundary

The current head-unit artifacts expose HMI/navigation clients, Screen/LayerManager/output drivers and HUD control/status proxies. They do not contain an identified matching Supra cluster/HUD root-renderer binary. Factory widgets reaching the windshield prove those paths are routed; they do not expose a shared parent framebuffer, coordinates or z-order to the application.

The new named-case launcher completes the executable **widget** portion of the batch. It cannot be relabeled a main-canvas test. Main-root work requires a receiver-side implementation or a traceable public interface with a drawing and removal contract. No guessed root writes, provider impersonation or oversized images are included.

## External cross-check

A fresh indexed-source search on19November did not produce a matching root-renderer implementation. The directly relevant [Supra Android Auto source documentation](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/main/milestone-7/readme.md) describes the J29 B006 navigation graph for cluster/HUD arrows. That is consistent with our known structured guidance path; it is not a demonstrated whole-windshield drawing API. Search coverage is limited and is not proof no implementation exists. Credit Sq00ky/nanaisu and ryseek for their respective guidance and native-video reference work.

See [whole-system capability map](HUD-CAPABILITY-MAP.md), [main control trace](MAIN-HUD-CONTROL-TRACE.md), and [canvas batch](NEXT-CANVAS-SESSION.md). V1 and its installation remain unchanged; no vehicle connection or Hz tests were performed.

## Receiver-side source follow-up

[Root scanout review](RECEIVER-ROOT-SCANOUT.md) traces a concrete BO03 receiver reference through separate HUD output, framebuffer mapping, pitch and pixel decoding. It is not a matched Supra receiver or a working network pixel binding. This advances the receiver architecture evidence without claiming root access.
