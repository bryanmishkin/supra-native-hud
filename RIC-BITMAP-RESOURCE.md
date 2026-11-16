# RIC bitmap upload format and binding

16 November 2026. Static evidence: NavNBTEvoController SHA256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`. No vehicle connection or transmission.

## Upload body recovered

The request at `0xbbde70` calls header builder `0xba0864` with method **3** at `0xbbdf78`. Body serializer `0xbbddf8` writes these fields without wire padding:

| Field | Wire form | Evidence |
|---|---|---|
| Instance handle | u32 big-endian | first `0xba2ff0` call |
| Resource ID | u32 big-endian | second `0xba2ff0` call |
| Resource type | u8, enum 0..11 | `0xba8128` |
| Variant payload length | u32 big-endian, excludes tag and this length | `0xbbdcc8`, backpatch at `0xbbddd8` |
| Variant tag | u32 big-endian | `0xbbdd38` |
| Variant payload | exact preceding byte extent | member dispatch `0xbbdc90` |

The bitmap sender at `0xab3d00` constructs its variant using `0xaafc48`, which explicitly stores **tag 2**. This connects the name `sendBitmapImageResource` to the wire type rather than guessing from ordinal order.

Bitmap tag 2 dispatches to `0xbb63e8`; tuple `0xbb6350` serializes base `0xbb4ee0` and byte array `0xbb58d4`. The base follows `0xbb4e48` -> `0xba8248`/`0xbb4334`. The payload is:

1. Inner resource ID: u32 big-endian.
2. Inner resource type: u8 enum 0..11.
3. Resolution pair: exactly two u16 big-endian values, no array-length prefix (`0xbb4184`).
4. Image byte count: u32 big-endian.
5. Image bytes: exactly that count.

Thus a bitmap request body is **30 + image-size bytes**. No separate PNG/JPEG/RLE selector was found in this traced structure. Image encoding and accepted resource type must not be guessed from the variant tag. The inner identity is populated from the same sender-side record as the outer resource arguments. The decoder reports disagreement rather than concealing it.

## Binding is a separate operation

`buildBitmapImage` at `0xaa78a0` searches 0x3c-byte resource records beginning at job+0x31c for the requested ID at record+0x10. On a match it constructs a bitmap resource object through `0xaa4ab0`, appends it to job+0x574, and returns success; absent ID returns false. The constructor stores ID, type, dimensions and image data; this staging operation is not by itself visible-model binding. Upload alone is not a display command and establishes no coordinates, visible slot, priority or independent client ownership.

A further caller trace reaches the actual detailed-maneuver branch. `0xaa7c20` builds detailed maneuver data; at `0xaa7d50..0xaa7d78` it copies an image resource ID into job+0x3dc, sets the adjacent image-reference type byte at +0x3d8 to 2, and calls `0xaa7b44` to stage the matching resource. That helper's local kind selector is 0=SVG, 1=bitmap, 2=picture-in-picture. These local kind values are **not** the resource-wire enums or union tags. This is a concrete resource-reference path within factory detailed navigation, not evidence of a separate overlay, free XY positioning or an accepted new client's graph. A second caller at `0xaa8900` stages referenced resources while building a resource-ID list.

The native GV bitmap parser at `0xd4b1cc` reads resource ID, its internal resource enum, two dimension values and image length/data. The GV parser's internal enum range 0..8 is distinct from the wire resource enum range 0..11. Do not interchange those enums or treat retained GV memory as a current frame.

## Implementation and validation

`tools/ric_resource.py` provides:

- Strict offline decoding of method-3 request bodies and complete SOME/IP request packets.
- Bitmap payload decoding with nested extent/enum checks and image hashes.
- A bitmap-body encoder with explicit arguments, no default identity and no network sender.
- Opaque preservation of untraced variants as tag/length/hash metadata.

The 12 added tests cover a fixed synthetic byte vector, every truncation, nested lengths, invalid enums, mismatched inner identity and packet envelope rejection. The full suite passes **119 tests**.

The two saved engine-running windows contain **five** method-3 requests, all resource type 3 / variant 4, and five empty successful method-3 responses. The new envelope decoder accepts every request with zero errors. There are **zero bitmap variant-2 uploads** in these windows. Responses were counted, not correlated across TCP connections. This validates the envelope against real traffic; bitmap payload validation remains static plus synthetic, not vehicle acceptance.

## New documentation lead, kept distinct

[KOMB_J29 diagnostic documentation](https://github.com/emdzej/ediabasx-docs-sgbd/blob/b644de8fbfbb4b207f57794e3c7894dc1dc58627/docs/sgbd/KOMB_J29.md) names the J29 cluster and describes software identification and a built-in test-pattern routine. The pattern routine chooses stored images or a color; it does not provide arbitrary image upload or an app-owned surface. Its generic routine-control interface includes stop, but the published argument table does not establish an automatic expiry. It is not being packaged as the tachometer drawing test. No diagnostic routine was run.

Further exact-interface and J29 firmware searches did not return a matching RIC server implementation or cluster firmware image. The user confirmed no existing programming-data set is available; no request to supply it is pending.

## Readiness

This closes the upload-format gap, not the whole drawing transaction. The independent test still needs accepted session/resource configuration, a complete visible maneuver/model binding and verified release behavior. The codec is not an executable vehicle drawing test, and the test-pattern diagnostic is not a substitute. No additional car session is requested.
