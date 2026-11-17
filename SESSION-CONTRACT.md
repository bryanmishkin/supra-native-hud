> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# RIC session, routing and release contract

16 November 2026. Static evidence applies to NavNBTEvoController SHA256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`. No vehicle connection or transmission was made during this analysis.

## What is now decoded

| B006 operation | Method | Request body | Successful response |
|---|---:|---|---|
| Create | 1 | Three length-prefixed strings, then three big-endian 32-bit version words | Big-endian 32-bit candidate handle, then a byte-length-prefixed array of configuration variants |
| Initialize | 4 | One big-endian 32-bit handle | Generated callback reads no response body |
| Dispose instance | 7 | One big-endian 32-bit handle | Generated callback reads no response body |
| Dispose resource | 8 | Big-endian 32-bit handle and resource ID | Generated callback reads no response body |

Method IDs are supplied to header helper 0xba0864 by the actual generated request functions, rather than inferred from strings. Scalar serializer 0xba2ff0 writes four big-endian bytes. Initialize/dispose/resource serializer entry points are 0xba3058, 0xba3098 and 0xba305c. Methods 4/7/8 above apply to **B006**, not the distinct B00E list service.

Create tuple code 0xba3ba8/0xba3c40/0xba4090 visits string objects at +0, +0x1c and +0x38, followed by a version tuple at +0x54. The string serializer 0xba3a40 writes a 32-bit byte length, FEFF BOM, UTF-16BE code units and a terminating NUL. Its BMP conversion is explicit; the offline decoder deliberately accepts only printable ASCII identity text because that is the verified factory subset. Version tuple code 0xba3460/0xba34f8 writes three 32-bit words. The traced factory IC request uses BMW.IC.Guidance / ICGuidanceControl / BMW and 3,3,1. These identify the existing factory client, **not an identity to impersonate or proof that another identity is accepted**.

Create response code 0xbd0794 reads the handle and array. Array code 0xbd0620 enforces a byte extent; variant code 0xbd0460 reads payload length and a 32-bit type tag, then consumes that payload extent. The client stores the handle at +0x1c in 0xab3108, and passes the returned array to 0xa2625c, logged as setAllConfigInfo. This is negotiated model configuration, not a surface/ownership grant established by this evidence.

Static configuration consumers include bitmap type 33 (resource range/count and RLE24/RLE32/PNG/JPG flags), composite bitmap type 34, picture-in-picture type 35 (resolution, color-depth and packing information), text type 36, and high-guiding image information type 39. These are configuration-variant tags, not drawing model IDs or display selectors. Their actual returned values for this Supra/client are not captured. The decoder keeps configuration bodies opaque and never enables drawing from the mere presence of a tag.

## Windshield selection: narrower uncertainty

In handler 0xa7a0cc, `r7` is the incoming notification and `r4` the owning object. The code compares incoming selection at notification-data+0x18 with the cached internal HUD flag at owner-data+0x18.

| Cached HUD state | Incoming selection | Result |
|---|---:|---|
| false | 0 | Set cached flag true; branch logged Kombi switch to Hud |
| true | 0 | No switch required; send completion |
| false | 1 | No switch required; send completion |
| true | 1 | Set cached flag false; branch logged Hud switch to Kombi |

Anchors: comparison 0xa7a228..0xa7a264; no-op completion 0xa7a28c; state updates/logs 0xa7a2a4/0xa7a2d4; incoming-selector branch 0xa7a51c. Machine code treats nonzero alike, but the offline helper only accepts observed/known values 0 and 1.

Thus **0 selects the HUD and 1 selects Kombi in this factory navigation sink state machine**. This does not mean every factory HUD element disappears when selection 1 arrives, does not describe whole-screen ownership, and does not supply a client-callable allocator. B009 is an incoming switch event plus completion, not a demonstrated API to request a second arbitrary overlay. The 460/237 resolution pair remains insufficient to define our drawable region.

## Cleanup is explicit, not a proved expiry guarantee

The factory disposal path at 0xab2180 checks its active flag and sends the stored instance handle through MyRicDisposeCall. Its sole direct caller found in the text section, 0xab2780, invokes disposal, releases local helpers and clears the local handle at 0xab27a0. This trace does not demonstrate that the remote object has disappeared before that local clearing.

A successful empty response to method 7 is protocol acknowledgement, not visual proof of cleanup. The traced create/initialize bodies expose no TTL field. Disconnect cleanup, server-side expiry, duplicate identity handling and independent overlay policy are not established by the client executable. No watchdog that merely kills our process may be presented as guaranteed remote-image removal.

## Implemented and checked offline

`tools/ric_lifecycle.py` decodes a single saved, fully framed B006/interface-1 SOME/IP message. It validates envelope, version, body bounds, identity subset, configuration extents, and lifecycle body widths. Unknown variant payloads are retained as tag/length/hash metadata rather than guessed capabilities. Every result explicitly leaves independent ownership, destination and remote cleanup unproven. It has no network sender or packet encoder.

```
python3 tools/ric_lifecycle.py /private/single-message.bin
```

The full suite passes 101 tests, including 19 lifecycle/routing/configuration tests. Applied to the two new engine-running captures, the decoder accepts seven B006 method-4 requests and seven replies with zero framing/decoding errors. No create or dispose exchange is present in those captures. Factory initialization is not a new app allocation.

## Exact drawing-test boundary

The marker test remains **specified but not executable**. A future implementation must use its own identity, inspect the returned model/resource configuration, identify an owned resource range and windshield binding, create one bounded marker using an accepted resource schema, then dispose that resource and instance with correlated replies and visible disappearance. No factory handle or captured graph may be substituted.

The missing evidence is now precise: server acceptance/ownership rules for a distinct client; the actual negotiated resource configuration and its binding to a windshield-visible model; and remote lifetime behavior on failed release/disconnect. Those rules live on the cluster side of the protocol and cannot be proven from the captured head-unit client code alone. The cluster renderer/server implementation is not in the identified captured executable set. An external server specification or implementation could resolve them offline; the current captures cannot.

Do not request another generic car session. Do not call the passive decoder, a simulated successful create, or a successful factory initialize a drawing test. Continue with resource/model schema tracing, and keep unsupported ownership/cleanup assumptions explicit.

## Bitmap configuration payload (static-derived subset)

Tag 33 dispatches through 0xbcf154. Its tuple chain reads: one-byte configuration-kind enum (0..39), one-byte resource-type enum (0..11), big-endian u32 element count, big-endian u32 element offset, exactly two big-endian u16 resolution values, and four one-byte boolean enums in RLE24/RLE32/PNG/JPG order. Total: 18 bytes. This follows the deserializers, not the in-memory structure offsets, which are different.

Anchors: prefix 0xbc13b8 -> 0xbc136c -> 0xbc12e4; resource enum 0xbc6570; count/offset 0xbc68d4/0xbc6964 -> 0xbc11f4; resolution 0xbcc230 -> 0xbcc138; flags 0xbc60d4; bitmap consumer 0xa26134. `decode_bitmap_config` validates this exact subset independently of the envelope decoder. It does not equate the inner enum to the outer variant tag without evidence, invent resource-type names, infer coordinate orientation, or treat resource count/offset as exclusive ownership. Unknown or extended payloads fail this subset rather than silently guessing.

Tests cover field order/endian decoding, truncation/trailing bytes and invalid enum values. These are synthetic format checks; no actual tag-33 create-response payload is present in our captures.
