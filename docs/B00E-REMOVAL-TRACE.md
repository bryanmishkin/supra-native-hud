# B00E resource checking and removal: independent HMI trace

19 November 2026, offline only. V1 unchanged. This establishes the list service's generated client contract independently of B006; it does not establish allocation rights or prove live B00E bitmap cleanup.

Captured HmiMain3D SHA-256: `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`.

## Service and body contracts

`CSomeIPRICServiceListClientBase` header helper at `0x2898c20` explicitly loads service **0xb00e** at `0x2898c60`, and interface version 1 at `0x2898c44`. Thus these traces belong to the intended service.

| Operation | Method | Exact body | Successful reply |
| --- | --- | --- | --- |
| checkResource | 2 | handle u32 BE, resource ID u32 BE, resource type u8 (0..11) | Exactly one Boolean byte, 0 or 1 |
| disposeResource | 8 | handle u32 BE, resource ID u32 BE | Generated handler reads no body fields |

`requestRic_checkResource` at `0x289da30` sets method 2 at `0x289da98`. Body helper `0x289d9c8` serializes the first two arguments through `0x27bf894`, which explicitly emits four big-endian bytes, then the third through `0x287de50`, which rejects resource types above 11 and emits one byte.

`handleRic_checkResourceResponse` starts at `0x28a6028`. It calls trampoline `0x28a6024`, which branches to `0x2879e20`. That function reads one byte through `0x270fd94`, compares it with 1 at `0x2879e44`, and branches to error for larger values. An adjacent enum deserializer at `0x28a5f34` accepts values through 39, but is **not** this handler's decoder. Adjacency must not be mistaken for a call edge.

`requestRic_disposeResource` at `0x2899038` sets method 8 at `0x28990a4`. Its helper `0x2898ff8` emits the two arguments through the same BE-u32 writer. The named response handler at `0x2898ac8` forwards the request identity to its callback and reads no body fields. Our proposed strict decoder should require an empty successful reply rather than accept arbitrary trailing bytes merely because the factory handler ignores them.

Illustrative body vectors, **not instructions to delete the factory resource**:

- Check handle 100, ID 0x01000000, type 1: `000000640100000001`.
- Dispose same tuple: `0000006401000000`.

These IDs are examples only. The advertised shared pool does not grant ownership.

## Visible withdrawal and cleanup sequence

The retained factory radio/phone/voice captures independently establish a method-9 focus-model update: model ID `0x65`, type `0x2e`, variant 3, selected reference replaced with `0xffffffff`; method 4 follows. See [decoded factory payloads](HUD-FACTORY-PAYLOADS-2026-11-19.md). This is actual factory focus withdrawal, not deletion of an uploaded bitmap. Model 0x65 is factory-owned and must not be blindly overwritten or disposed.

A bounded custom-image test must establish its own model/reference plan first. The required sequence is:

1. Confirm admission, ownership, and absence of the specific candidate image slot before uploading.
2. Upload only the owned image and bind only through the independently traced model field.
3. Withdraw the test's visible reference/focus and commit using the proven model semantics; preserve factory state.
4. Dispose only that image ID with method 8; require a uniquely correlated success reply.
5. Re-check the same handle, ID and type with method 2; require an exact false Boolean reply.
6. Independently confirm the test graphic is absent from both displays. Resource absence alone cannot prove rendered-cache removal.

Timeout, error, malformed reply, changed handle, uncertain request correlation, or incomplete reference withdrawal is an unresolved cleanup result—not permission to dispose the whole instance. Do not use method 7 on factory handle 100 as a fallback.

## Offline validation and remaining readiness

Private exact-body codec vectors passed for a nine-byte check body, eight-byte disposal body, strict Boolean replies, rejection of empty/non-Boolean/trailing replies, and empty disposal acknowledgment. No live sender or connection is included. Exact static disassembly and the offline codec are retained under the private `b00e-binding-tests-2026-11-19/removal-agent` output directory.

Still required before a B00E image test: concrete image-field binding, collision-safe shared-resource/model ownership, and a complete model-reference withdrawal plan. The method contracts above resolve the resource-query/delete portion; they do not by themselves make the larger-display test ready.
