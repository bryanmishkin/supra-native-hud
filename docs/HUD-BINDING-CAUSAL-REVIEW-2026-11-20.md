# Pixel binding: causal review of the retained evidence

Offline analysis, 20 November. No vehicle connection or V1 modification. Owner deferred V1 restoration after the session; installed files remain unchanged, but running V1 has not been reverified.

## What the new packet comparison actually proves

`tools/analyze_pip_trial_pair.py` correlates the saved direct requests and replies with reassembled PCAP traffic. Both recordings have no stream parse errors. All 20 request/reply pairs appear exactly once in each recording. Comparing their application bodies identifies only transaction 6, method10/type29, bytes24–25 as different; these lie within the numeric distance member. Both cases receive selection1, and neither receives a later selection0.

The first graph command follows selection by267.092ms in the461 case and256.620ms in the69 case. That does not justify reversing the order: three independent factory recordings also show subscription/selection before the factory guidance graph. In the MOST recording, selection precedes the first state update by1.354s; another factory selection precedes distance and descriptions. In the navigation-watched and navigation-cycle recordings, RoadInfo follows selection by554ms and799ms respectively. Separate V1 and factory TCP flows must not be conflated.

The recordings contain one advertised B009 endpoint per trial, not competing producers. Repeated subscription ACKs target the same endpoint. Factory B006 discovery renewal continues, but no factory B006 application update is captured in these windows. This does not exclude receiver state retained before recording; it supplies no reason to terminate a factory subscriber.

**Disposition:** retire the distance pair as a proposed repair. `run_hud_selection_session.py` requires explicit `--repeat-known-negative-control` for pause/case; observation, audit and restoration remain available. No reordered, alternate-distance or forced-completion test is justified by these results.

## B00E: encoding and cell-state checks

The captured HMI ARM Roadbook RIC decoder executes the actual failed36×36 ruler stream successfully:880encoded bytes produce1296expected pixels. Eleven native cases now include literal/repeat boundaries127/128/255, solid8×8, alternating8×8 and runs crossing a conceptual scanline. All match expected channel values, with no intercepted decoder callbacks. `verify_hmi_rle_decoder.py` pins the captured HMI hash.

This is stronger than confirming a serializer copies bytes, but it is **head-unit decoder execution, not cluster receiver execution**. The HMI content producer copies already-compressed type8 content into its bitmap resource; native HMI encoder output has not been recovered. No compression mismatch has been demonstrated.

Six executions of the Entertainment builder, crossing bitmap/text references with provider states0/1/2, show the same independent row-state provider call and unchanged state storage. The trailing ListElement byte is not a bitmap-format discriminator at this callsite. Carousel has four references per item; its final three bytes belong to the whole model, not each bitmap cell. Their full semantic names are not established. A flag toggle is not an evidence-backed fix.

UnifiedCall, Notification and Popup wrap the same GenericListModelStruct; their inspected serializers do not add a dedicated raw-image member. Factory phone/door/voice captures show their model transitions but no type1 bitmap upload. Wrapper availability is not a new canvas.

Four additional zero-intercept native executions confirm the bitmap allocator cursor increments/wraps within its configured ten-slot range and copies the chosen ID unchanged into both outer and inner resource headers. The traced caller stores that return value directly in the content cell. No alternate client prefix or second translated image ID is established. `verify_b00e_bitmap_identity.py` preserves this check; it does not emulate receiver lookup.

## Display attachment map

| Path | Producer evidence | Actual visible result | Remaining distinction |
| --- | --- | --- | --- |
| B006 inline road icon | RLE32 resource and RoadInfo binding | Custom markers and V1 in windshield and cluster | Known bounded working route; no proof of main compositor access |
| B006/B009 PiP | Correct native pixel publication, descriptor and sink handshake | Custom277×160 marker in cluster; factory arrow in windshield | Receiver selects cluster1; no observed HUD0/custom windshield delivery |
| B006 detailed picture | Resource/model transactions accepted and removed | Factory roundabout only | ACK/resource presence does not prove visible attachment |
| B00E content cells | Native provider can return bitmap reference; uploads decode on HMI | Exact target text blanks; custom ruler absent | Receiver lookup/layout support remains unproven |
| B00E factory frame | Factory model replay renders rounded frame and Presets | Windshield frame and factory content | Widget outline does not expose arbitrary interior pixels |
| Height-adjustment corners | Captured HUD control events | Factory full-view corners | Scalar calibration control, not demonstrated image-upload contract |

The whole windshield compositor remains a distinct goal. Neither the800×480 producer backing store,320×320 structured guidance definition, nor a128×128 bitmap resource limit is evidence of an acquired arbitrary drawing surface. Existing captured binaries are head-unit producers, not the matching cluster receiver binary.

## Reproduction and next evidence gate

Run the paired analyzer offline against the private session folder; run the native decoder verifier against the pinned HMI and failed ruler request. Keep those OEM inputs and packet bodies out of Git. Private output folders retain timestamps, exact packet references, six native cell-state cases, and all eleven native decoder cases.

The next useful proof is an actual difference in resource lookup or attachment between factory image-producing code and our transaction sequence, or a receiver-visible field whose routing effect can be established from captured native code. Continue that trace before admitting a car test. A successful local decoder, ACK, factory frame, or different selector alone cannot satisfy that gate.

## Subsequent concrete candidate

The working model40 road list advertises10entries/10icons, and native execution proves multi-image serialization. This is a distinct, supported structure absent from prior live tests. See [two-image expansion batch](ROAD-LIST-EXPANSION-TEST-2026-11-20.md). Its physical arrangement is the next measurement; it does not repair PiP destination selection or establish a full-screen canvas.
