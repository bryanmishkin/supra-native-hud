# Actual factory payloads: B011 and B00E

Offline decoding of the complete 19 November captures. V1 and vehicle untouched. This resolves payload direction and resource families; it does not establish ownership of a new display session.

## B011 is returning check-control content to the head unit

Four method-1 requests go from HU `.119:65477` to cluster `.96:30501`. Their bodies are exactly two bytes: `000f`, `0000`, `000f`, `0000`. Four replies reverse that direction and correlate by client/session. The cluster also sends four method-8002 notifications.

Notifications carry UTF-16 text `Door open.` or `No entries.`. The method-1 replies carry the corresponding text and a complete PNG. There are two unique PNGs, each 81×81, 8-bit grayscale with alpha (IHDR color type 4). Every PNG chunk CRC verifies, and IEND terminates each extraction. The door PNG was visually inspected: it is a top-down open-door car symbol. Original icons remain private OEM evidence, not public assets.

This is **not** evidence of HU-to-windshield bitmap upload. It is cluster-to-HU retrieval of factory alert content. HmiMain3D contains `CSomeIPKombiInterfaceClientBase::requestRequestCCMessage`, response/notification handlers, and `CCMessageWithSymbolStruct` names, consistent with that observed exchange. A symbol-name match alone is not an independently executed service/method mapping.

## B00E models and visibility references

All observed model/resource envelopes in the three recordings validate their length and repeated ID/type. Handle is 100. Method 4 is handle-only; methods 3/9/11 use the existing update-envelope shape.

| Owner-visible graphic | Method 11 model | Type | Variant tag | Captured behavior |
| --- | --- | --- | --- | --- |
| Radio | 0x66 | 0x16 | 3 | 73 entertainment-model updates; text resources and references, selected via model 0x65 |
| Phone | 0x68 | 0x2d | 9 | Four identical model writes; state resources 0x70/0x71; focus 0x65 points to 0x68 then FFFFFFFF |
| Voice | 0x6e | 0x2f | 10 | Twelve state writes; focus 0x65 points to 0x6e then FFFFFFFF; separate text resource 0300002c |

The HMI's CommonAPI model variant type list places EntertainmentListModelStruct third, UnifiedCallListModelStruct ninth and VoiceRecStateStruct tenth. This agrees with the captured tags; it is corroboration, not a claim that every field of those structures is decoded.

The exact focus update is a method-9 envelope with model 0x65/type 0x2e/tag 3; the trailing 32-bit word is the selected model ID, or FFFFFFFF on withdrawal. Each captured cycle is followed by method 4. Do not blindly replay these factory IDs: they are shared factory resources, not ours.

Radio resource method 3 includes 42 type-3/tag-4 text resources and two type-0a/tag-11 resources containing nested text (`Presets`, `Recent calls`). The firmware resource variant list labels variant 11 CompositeTextStruct. These are not large bitmap frames. The radio window includes one phone-model update, so it is not perfectly exclusive to radio content.

Phone has no method-3 resource creation in its captured window, so it refers to pre-existing resources. This does not prove it has no images. Voice creates one text resource, containing `Please wait…`; its state bodies change references ending 005c/0059/005a/005b. Their semantic labels are not assigned without tracing the relevant fields. The capture has no PNG payloads in B00E and no known native PiP descriptors.

## What this eliminates and what remains

Door, phone and voice cannot be treated as interchangeable demonstrations of an arbitrary PiP canvas. B011 supplies factory check-control assets in the opposite direction; B00E selects structured factory-rendered models. A large visible region does not imply unrestricted pixels at that size.

The concrete next implementation target is the B00E resource/model configuration contract: whether an image-bearing field can reference a separately owned bitmap, what geometry limits the receiver reports, and how that model is created and removed without overwriting factory objects. The observed focus/withdrawal messages provide exact evidence for that trace, but no independently owned B00E model has been established. Therefore no live sender or new marker is enabled by this work. The old failed PiP runner remains retired; no speculative car trip is requested.

## Reproduction

`tools/extract_hud_factory_payloads.py CAPTURE_ROOT NEW_OUTPUT` reassembles strict PCAP TCP streams, extracts B011/B00E messages, finds bounded UTF-16 fields and validates/extracts PNGs. It never connects to a vehicle. Output is private: text may contain phone/radio data and PNGs are OEM content. Replay of all four retained complete recordings passed; extracted PNG files were byte-identical to the initial analysis. Keep unknown bytes rather than coercing them into guessed coordinates.

Public source contains the extractor and this derived report only. Drive contains raw decoding, original icons, checksums and source revision.
