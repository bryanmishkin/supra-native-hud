# DisplaySink protocol implementation and captured replay

Offline only. V1 unchanged. This implements the missing protocol codec and negotiation state, **not a verified larger-windshield fix or a runnable car candidate**. The failed live runner remains retired.

## New evidence from retained traffic

The factory PCAP previously used for navigation analysis also contains complete B009 service-discovery exchanges. A deeper UDP review found:

- 49 HU subscription/unsubscribe packets, advertising the actual TCP endpoint `160.48.199.119:65497`, sent via UDP 30490 to the cluster.
- 94 cluster subscription acknowledgments (including repeated acknowledgments).
- Subscription TTL 3 seconds in the retained factory exchange; TTL zero releases it. Do not assume the G30 reference's 30-second TTL/10-second renewal is the factory Supra cadence.
- Two receiver selections and matching TCP completions, already inventoried by `audit_pip_sink.py`: scale 1, 460×237, selection 1, completion `0100`.

Capture SHA-256: `0976202b21605829b4bef74d62dd1b724b7dc1fce85c23e4a63e8ccd696aced3`. These are observed factory-client identities, **not an available endpoint for our app to take over**.

## Implemented code

`tools/pip_displaysink.py` is an offline, socket-free protocol component:

- Encodes the single-entry B009/event-group-1 subscription and TTL-zero unsubscribe, using an explicit IP, connected TCP port, discovery sequence and TTL. No vehicle IP is a default.
- Strictly decodes that subscription and the recorded ACK shape. Rejects wrong service/group, malformed lengths/options, unusable endpoint values and unsupported variants.
- Handles fragmented TCP selection messages within bounded storage. Produces the completion for the **received** selection rather than requesting or fabricating a different destination.
- Requires an acknowledged, unexpired subscription and explicit completion-send confirmation before reporting negotiation complete.
- Invalidates the selected destination on unsupported selections, protocol errors, negative/zero-TTL ACK and close. A pending completion is not completion.
- Never reports receiver pixels verified or windshield ready. It opens no sockets and starts no Guidance or native output.

The eventual transport owner must validate source endpoint and connection identity, use monotonic time, manage bounded TCP writes, renew before expiry, send TTL-zero unsubscribe, close only its own sockets, and perform independent image cleanup. These transport/ownership operations are **not implemented by this socket-free state component**. It must not be wired into a live runner until our producer's endpoint ownership and pixel association are established.

## Verification

Private replay reconstructs the 49 subscriptions from decoded fields and compares every byte with the recording. All match. It feeds 94 ACKs and the recorded selections through the state component, splits event frames across reads, and compares generated completions with both actual recorded completions. Both match and complete within the captured lease.

24 focused PiP tests pass. New cases cover expiry, negative ACK, unknown HUD tuple, partial reads, pending-completion mismatch, oversized data, truncated SD packets, wrong event group, unsubscribe and close. These tests are protocol verification, not a cluster simulator. They do not validate image delivery.

## What remains unresolved

Selection 1 is Kombi in the retained target controller. The new replay therefore proves a **factory cluster sink handshake**, not a windshield grant. Our desired larger HUD image still lacks a demonstrated association between an independently owned producer endpoint, native Screen pixels, and a receiver-selected windshield destination.

Adding a subscription to the existing failed runner without resolving that association would still be speculative. The implementation deliberately has no switch that forces selection 0 or treats an arbitrary geometry as supported. No additional car session is requested on this evidence.

This replaces guessing the handshake bytes with captured, repeatable protocol handling. It does **not** establish that the missing handshake was the sole cause of the two failed marker tests. See [startup omission and scope correction](PIP-SINK-CONTRACT-GAP-2026-11-18.md).

## Attribution

ryseek's G30 native PiP source in the Sq00ky/nanaisu project identified the subscription-before-Guidance sequencing. The wire implementation here is checked against retained Supra traffic. No external runtime source is copied. Preserve the existing [third-party notices](../THIRD_PARTY_NOTICES.md) and [pinned reference review](PIP-G30-REFERENCE-2026-11-18.md).
