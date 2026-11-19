# HUD packet audit: distinguish uploaded resources from bound pixel transport

19 November 2026. Offline analysis of saved captures, alongside a separate REA/native-firmware investigation. No car connection, installed V1 change, or Hz test.

## Evidence coverage

`tools/audit_hud_capture_corpus.py CORPUS NEW_PRIVATE_OUTPUT` deduplicates classic PCAPs by SHA-256, uses the existing strict TCP reconstruction, and retains exclusions and unparsed streams. The current corpus has 46 distinct PCAPs; one fails TCP continuity and is excluded. Counts are retained observations, not independent tests or drives. Repeating the audit produced identical output. Raw resource bodies remain private.

The parsed corpus contains 909 unique B006/B00E method-3 resource bodies:

| Source | Distinct bodies | Meaning |
|---|---:|---|
| B006 client 0x5348 | 580 | Our bitmap uploads, including proven V1 rendering; not factory bitmap examples |
| B006 client 1 | 7 | Factory text resources |
| B006 client 0x5350 | 2 | Our experimental PiP descriptors, 320×200, depth variants 0/1 |
| B00E client 1 | 312 | Factory text resources |
| B00E client 1 | 8 | Factory composite resources, including Presets/source headers |

There is **no factory bitmap upload in this parsed corpus**, on either service. This does not prove the factory never uses bitmaps. It prevents citing our own experiment as a successful factory-pixel binding example.

## Failed B00E trials: concrete exclusions

Audited five 36×36 ruler trials: both Carousel content words, both selected Entertainment cells, and the full-menu icon replacement. Three factory/frame controls were audited separately. All 281 saved request/reply pairs matched service, method, client/session, protocol/interface, success kind/code and message lengths.

Each trial uploaded the same nonempty six-color, fully opaque bitmap. RLE32 decoding and exact re-encoding passed. The sent candidate and restored model bodies match the retained files. Existing journals prove resource presence while observing, exact factory-model restoration, image disposal and subsequent absence. Owner reports remain the visibility authority: no custom ruler rendered.

The firmware investigation separately executed the captured B00E BitmapImage serializer and reproduced the failed ruler's payload byte-for-byte. Native dimension storage is a vector, but its wire writer emits exactly two big-endian u16 values, not a vector-length prefix. Therefore adding a dimension-count prefix is not a fix.

The separate native analysis also executed the captured HMI RIC `rle32RGBAtoTGA` decoding loop with no callback substitutions. It decoded the failed ruler to all 1,296 expected pixels and passed literal/repeat boundary cases. This establishes compatibility with that captured HMI codec; it does not substitute for executing the cluster receiver decoder.

These facts rule out empty fixture, opaque-alpha omission, missing sent resource, uncorrelated ACK, and the tested serialization mismatch. They do **not** establish receiver decompression, client/session resource lookup, a supported widget-image binding, or available visible geometry. Do not repeat the same field substitutions at larger sizes and call that a canvas test.

## PiP: missing transport handshake is visible in the recordings

The first failed PiP capture, its independent on-unit capture, and the revised failed attempt contain respectively 114, 113 and 114 B009 discovery entries. Every entry is OfferService (type 1). None contains SubscribeEventgroup (6), SubscribeEventgroupAck (7), or a B009 TCP message in the parsed capture scope.

Factory navigation recordings do contain subscriptions/ACKs, followed by B009 selection/completion messages. Across five captures the eight retained selection events all carry `3ff000000000000001cc00ed01`: scale 1.0, dimensions 460×237, selection 1. Corresponding completion bodies are `0100`. Static mapping identifies selection 1 as Kombi; selection 0 is HUD. No selection-0 event occurs in the parsed TCP corpus. In the 19 November factory-navigation recording, both selection events match an unexpired subscription for the exact TCP endpoint, an unexpired acknowledgment from the same server, and a same-selection completion within three seconds. The failed first/revised attempts have none of those events.

The two 320×200 resource descriptors are our experiments and contain no pixel array. A descriptor, native window and factory turn arrow therefore did not establish a pixel-bearing receiver connection. The next PiP implementation must establish and record the actual sink subscription, selected destination, completion and producer/session association **before** claiming marker delivery. A successful selection-1 negotiation would prove a cluster sink, not automatically a windshield sink.

## Main HUD outline and local surfaces

All eleven retained local surface-1056 snapshots are byte-identical across navigation, radio, phone, voice and door visible/closed states. They report 0×0 size, invalid native-surface handle, zero frame/draw/update counters and no attached layer. The owner saw windshield graphics during those states. Thus surface 1056 was not the active pixel carrier in those snapshots. This does not exclude every head-unit surface or all possible PiP use.

The 120-second height-control observer saved 1,273 rows, with no dropped/bad rows and zero target commands. Its scope is specifically E0/01 DevCtrl with an E0 tap filter, **not all MOST traffic**. Only two CA6 SETs and two responses were retained. The SETs differ in their height-adjustment byte (0a→0b); native code maps them to UI −1→0. They are not the separately traced setMode call, bitmap coordinates or pixel data. Consequently the recording does not prove that merely opening Height transmits an outline image or grants its interior as a canvas.

## What must be implemented or resolved next

1. **PiP connection:** implement the missing observed subscription/selection/completion path with explicit ownership and teardown, and trace its selected sink into the native producer job. Refuse to claim HUD readiness from a Kombi-only selection or from a local window. Do not reuse the arrow-only test unchanged.
2. **B00E receiver binding:** compare the real provider/model contract and receiver lookup semantics now that exact wire parity is established. No additional guessed resource field or size sweep is justified by the same evidence.
3. **Whole HUD composition:** retain it as a separate target. Height settings, menu outlines and local display dimensions are not an arbitrary root framebuffer. The current packets identify structured controls and widgets, not a root drawing API.
4. **Recovery:** preserve the diagnosed startup-failure trace. The failed V1 boot wrote a persistent lockout; the following restart honored it. After the diagnosed token was archived, the owner restarted, saw V1 return and disconnected. Installed binaries/configuration were unchanged. Never request repeated recovery restarts without inspecting the persistent gate.

No larger-display fix or new car-test readiness is claimed by this audit. The value of this pass is narrowing the implementation to observed contracts and rejecting previously repeated guesses.

Private evidence bundle: `hud-packet-deep-dive-2026-11-19`, including the corpus manifest, exact resource bodies, transaction audit, PiP subscription/selection observations, local-surface comparison, height-control scope and startup-cookie sequence. Native results are in `rea-firmware-2026-11-19`.

## Reproduce the native checks

The private HMI hash is pinned by both tools. Neither script connects to the car. Supply the captured HMI and saved B00E method-3 ruler request to:

```text
python tools/verify_b00e_native_wire.py --hmi CAPTURED_HMI --request SAVED_RULER_REQUEST
python tools/verify_hmi_rle_decoder.py --hmi CAPTURED_HMI --request SAVED_RULER_REQUEST
python tools/audit_pip_handshake.py SAVED_PCAP
```

The wire harness covers four metadata/payload cases; metadata-only cases are not valid drawing fixtures or admitted canvas sizes. The decoder harness covers the actual ruler plus seven repeat/literal boundary cases. Both were re-run from the repository copies. The packet audit was also repeated exactly. Dependencies use the existing ELF/Unicorn analysis environment.

REA 6.9.0 with Ghidra 12.2 successfully decompiled a provenance-tracked extraction of the HMI RIC decoder at its original virtual address, and the captured display-test utility. The decoder's 512-per-dimension/65,536-pixel checks belong to that head-unit adaptor, not the receiver canvas. The display-test utility targets rear-seat/head-unit outputs and is not a HUD test. Full-HMI auto-analysis did not complete; focused decompilation and direct instruction execution provide the evidence stated here. REA source: https://github.com/morluto/rea . No third-party code or OEM firmware is published with these scripts.
