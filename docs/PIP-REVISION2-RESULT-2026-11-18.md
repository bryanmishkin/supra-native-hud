# Revised PiP test result — 18 November 2026

**Failed visual test; cleanup and V1 restoration passed.** The owner saw a right-turn arrow in the windshield only, with no custom rectangle/cross. Changing the descriptor's depth from 1 to 0 did not make the image visible. The owner has unplugged. No further vehicle access is authorized by this completed session.

The tested source was `1ecf28b78421a734155d2068f61e1fc3279712c6`, branch `v2-ux`. This was the bounded, RAM-only revision-2 candidate, not a V2 install. V1 files, startup configuration and activation tokens were not replaced.

## What the new capture establishes

- The producer binding record matched the controller: description `0x0f000004`, resource `0x02000004`, backing 800×480, content 320×200, selected depth 0, packing 0, Screen format 8 and metadata ID bytes `0f000004`.
- Native producer posted **255 frames** and reported successful local cleanup.
- During first post and just before removal, `/dev/screen/0/dpy-2` showed `scene = win-15`, `windows = win-15`, OTHER2 800×480, pipeline 2 with RGBA8888/source 1. Its counter advanced **3 → 257**. Both active snapshots were complete, without read errors.
- The output was therefore active locally during the attempt. That is stronger than the prior before/after snapshots, but does not identify its physical destination or prove cluster reception.
- All **20** controller transactions received correlated protocol acknowledgments. The seven withdrawal/removal commands—methods 9, 9, 12, 11, 4, 9, 8—were acknowledged; a final check confirmed the selected PiP resource absent.
- Owner observation: **only a right-turn arrow, windshield only**. No custom marker; no larger image acceptance.

The direction-7 navigation description explains the requested arrow. Successful protocol calls and a visible navigation symbol did not validate the custom pixel path. `status: finished` in the raw result describes the completed command sequence, not visual success; `visual_pass` remains false.

## Recording integrity

The passive recorder ran 120.007 seconds, exit 0, **4,686 packets**, **1,017,704 bytes**, zero drops and zero interface drops. It transmitted no packets and was not promiscuous. Strict offline extraction produced 20 TCP directions without parse errors. No B009 messages occurred in this interval; the existing sink state cannot be inferred from that absence.

PCAP SHA-256: `a58ce81531c3d7e0d8ceb5777d48a20e7798df29278026a0cc1cb21d0c655f09`.

## Cleanup and return to V1

After the helper exited, the secondary Screen output returned to an empty scene with no windows. LayerManager still listed surface 9001 as an invisible, unbound placeholder: native surface `4294967295`, source/viewport zero, no layer, frame/draw/update counters zero. This was not treated as full surface deletion.

The owner confirmed the arrow gone and both displays normal, then performed the established volume-knob iDrive restart. After restart:

- The private PiP RAM directory and separate validation RAM directory were absent.
- Surface 9001 was absent; secondary output remained empty.
- All **13 V1 package files plus two startup configurations** matched the exact baseline.
- V1 hooks, enabled state, read-only filesystem protection, healthy supervisor, advancing heartbeat and advancing RPM frames were verified.
- All five permanent fault records were byte-identical to the pretest copies.
- Owner confirmed **V1 visible and updating**.
- The SSH master was closed before the owner unplugged.

## Implication for further work

The isolated depth change was **not sufficient**. It must not be presented as a successful PiP binding repair or repeated as the next supposedly ready test. The local producer is demonstrably active; the unresolved edge is its receiver/physical-path contract, including whether this target supports this backing/resource relationship. The G30 source is not proof of that contract on the Supra.

The next change needs evidence for that missing connection before another car visit. Do not cycle through IDs, dimensions, formats or outputs in the car. Do not infer a disconnected physical link solely from `WFD_INVALID_HANDLE`, or infer a sink choice from an interval without B009 traffic. Retain V1 unchanged. Credit to ryseek and the upstream Supra Android Auto contributors remains in the reference and third-party notices.

Private archive includes the exact tested kit, source, complete capture and streams, active output snapshots, request/reply evidence, owner observations, baseline checks and cleanup/restoration receipts. OEM/vehicle-specific data remains out of GitHub.
