# Pixel-path follow-up — 18 November 2026

Offline analysis of the [passive car capture](PIP-CAR-RESULT-2026-11-18.md). No vehicle commands, runtime edits, installation changes or new drawing test. V1 remains intact.

## What the new capture distinguishes

The recorded image uploads are **not evidence of a larger factory navigation image**. Separating TCP connections and resource IDs gives:

| Sender connection to receiver port 30502 | Resource requests | Interpretation |
|---|---|---|
| Head-unit source ports 65297 / 65298 / 65299 | 40 / 46 / 137 bitmap uploads respectively; all IDs `0x01000008` or `0x01000009` | Exactly the two V1 tach slots; 223 uploads total |
| Head-unit source port 65495 | Four text uploads, IDs `0x03000000`, `0x03000002`, `0x03000003`; no bitmap and no PiP descriptor upload | Factory maneuver-model traffic during owner-confirmed guidance |

These are observed connection identities for this capture, not stable port assignments or independent process attribution. The V1 identification also depends on its exact resource IDs and known model sequence. Both clients use handle 200; handle equality alone cannot separate them.

Factory model evidence on the latter connection:

- The active list (`0x21000000`) selected maneuver `0x0f000000`, guidance state 2. Its decoded description has `detailed_maneuver_id = 0xffffffff`, with coming-road, current-state and distance references. The active maneuver therefore has **no detailed-picture reference in these updates**.
- Two subsequent maneuver descriptions were also sent. One references model `0x31000000`, method-11 variant 10 (12 payload bytes); another eventually references `0x07000000`, variant 6 (54 payload bytes). These are not the traced variant-7 high-roundabout image reference. Their inner fields remain opaque; do not invent a pixel address from them.
- The only variant-7 messages were on V1-associated connections, with picture ID `0xffffffff`. They must not be presented as factory PiP activation.
- Guidance stop changes the list through states 7, 5, then 0, clearing the active reference. A new V1-associated connection uploads slot 9 about **0.4 seconds after** the final factory state-0 message (first upload timestamp uses the TCP span containing the message start).

Two B009 sink events precede the factory maneuver sequence. Their bodies are identical (`3ff000000000000001cc00ed01`); completion bodies are `0100`. The first event is about 2.57 seconds before the first observed active-list state-2 update; the second about 0.37 seconds before it. This is temporal correlation, not proof that the final selector value or the 460/237 pair describes a writable windshield rectangle. No creation/initialization exchange was captured.

## Where pixels are, and where they are not proven

The observed chain is consistent with:

`NavigationFully structured guidance → controller RIC model serialization → Ethernet receiver → factory rendering`

The last rendering stage is inferred from the model-only traffic plus the owner's visible-guidance confirmation. The capture does not include receiver implementation or exclude pre-existing resources and other transports. It does show that this observed guidance transition required no new bitmap or PiP upload on the captured B006 streams.

The previously traced native PiP branch is a different candidate:

`view type 0 → QNX Screen window / EGL window surface → downstream binding not established`

Live window 1056 is 800×480, assigned to display 1, but has no clipped visible area and unchanged first-buffer bytes across normal/navigation samples. Display 1 is HDMI1, 1280×480. The final display-2 metadata reports OTHER2 at 800×480, an empty scene, no windows, and no plane source. Merely finding a second display of the right size does not establish windshield routing.

The memory map **does** contain command rings for displayable IDs 7, 17 and 19 (`GVCommand` names, some truncated by pidin). Absence from the shallow shared-memory directory listing was not absence from the process. No `GVBitmap`-named mapping appears in this captured map. Historical command-buffer tracing identifies structured navigation records and controller consumers; the current map alone does not say which ring changed during this session. Do not label an old retained buffer payload as a current frame.

## Consequence for larger V2

Three distinct sizes must remain separate:

1. **150×36:** proven custom bitmap path used by V1/V2.
2. **320×320:** advertised PiP configuration, with a metadata-only resource descriptor. No demonstrated pixel transport or visible binding.
3. **800×480:** actual native window allocation, not demonstrated windshield output.

Increasing the first size or writing the third buffer does not implement the second path. The radio popup is also not proof of PiP use: this radio/navigation capture contains no PiP resource creation.

The next offline target is the consumer of the native window/session binding and the PiP resource-ID-to-image association, not further generic radio/nav recordings. An executable expansion test needs a traced pixel producer/transport, an explicit windshield binding, and owned cleanup. If those resolve only in receiver firmware or an unobserved initialization exchange, name that exact missing edge before requesting another car session. No larger-space live test is ready yet.

## Reproducibility and limits

The private evidence package contains a per-flow decoded model audit with offsets, original TCP-span timestamps, the analysis script, and the source capture package. Re-extracting the original PCAP reproduced all stream hashes and bytes; all selected resource/graph/guiding decoders completed without errors. Timestamp attribution is to the segment containing the message start, not receiver commit time. Framing consistency does not prove an initial application boundary. Route fields and OEM bytes remain private in Drive.
