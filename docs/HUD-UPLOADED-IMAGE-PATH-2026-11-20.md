# 408 × 132 uploaded-image preparation — 20 November 2026

The offline kit now contains a full-size coordinate marker and native receiver checks for cache insertion, exact pixel decoding, image fitting, built-in name selection and reference replacement/restoration. No vehicle commands were sent. V1 files and the prepared diagnostic-surface runner remain unchanged.

## Reproducible results

`tools/prepare_hud_full_surface_marker.py --output <new-directory>` creates BGRA, RLE32, PNG and a manifest. The 408 × 132 marker has distinct corner colors, border coordinates 0..407 / 0..131, horizontal lines at 35/66/96 and vertical lines at 149/203/300. Its encoded size is 5,928 bytes, below the older receiver cache's 0x14000-byte bound. Raw pixels: SHA-256 `21fbd7b8acb0b3f07eba992798d04d70695b610cd54abb2b156f80911b99230e`. Encoded bytes: `4f97f9f13aa3e63b01aecc02287a9d94fbbe004cf7719aad4f1ad76025453752`.

`tools/verify_hud_uploaded_image_path.py --image <004-main> --data <004-data> --marker <marker-directory> --output <report.json>` executes hash-pinned receiver code with Unicorn:

- Native insertion at 0x2b1ab0 and lookup at 0x2b21fe retain exact dimensions and all encoded bytes. The synthetic ID is 0x01000008, not a live allocation.
- Native decoder 0x2d303c produces all 215,424 pixel bytes exactly. Its allocation is intercepted; the 16-byte trailing guard remains intact.
- All 127 nonzero accepted TestBmp selectors, each with two RGB inputs, select names under `Imports#hud#hud_TestBmp#`. The 254 runs execute the selector/name slice; virtual resource-manager lookups are synthetic. This does not execute the real asset resolver.
- Native KI name translation at 0x2562c4/0x2562ee enumerates the 122-entry built-in table indexed by IDs 0x07000000..0x07000079. Both functions return null for the uploaded-image ID 0x01000008, selector 0x5c, first out-of-range ID 0x0700007a and 0xffffffff. This bounded translation is distinct from numeric upload-cache lookup; it does not rule out a separate resource-manager interface.
- Shared-reference assignment 0x2137d2 replaces and restores a synthetic brush+0x34 reference with correct reference counts. Both known paths use this assignment. It is not an external binding API and does not establish runtime texture compatibility.

The cache experiment uses the same synthetic storage for read/write buffers. It does not execute buffer commit, concurrency, transport admission, GPU rendering, actual texture creation or physical display output. The analyzed firmware is 004_000_003; the installed ECU reported 008_000_000. No raw-address vehicle patch is prepared or authorized by these results.

## Geometry checks that prevent another strip false positive

`tools/verify_receiver_image_geometry.py --image <004-main> --output <report.json>` now passes nine fit cases and seven decoder fixtures. Actual fitter 0x257060 yields:

| Image | Bound rectangle | Scale | Resulting extent |
|---|---|---|---|
|408 × 132|408 × 132|1|408 × 132|
|408 × 132|150 × 36|36/132|111.27 × 36|
|408 × 132|150 × 132|150/408|150 × 48.53|

All corner markers can survive uniform scaling into the strip. Seeing them is insufficient. A future uploaded-image test must establish the actual destination rectangle and compare physical height to the unchanged reference. The coordinate marker is not registered to V1's physical placement.

## Remaining binding trace, with concrete entry points

The full-size TestBmp node stores a bitmap brush at object+0x24 and sets its image reference at brush+0x34. The normal uploaded-image route is 246672 → 25740c → 257180 / 257348 → 2d303c; the brush assignment is in 257222. The missing connection is an externally reachable operation that directs that uploaded resource to the full-size node.

TestBmp's named-resource interface comes from object+0x10; its vtable is at manager+0x1c, with calls through +0x6c and +0x74. Widget initialization 19f68e stores the manager pointer. Resolve the actual manager implementation and its asset lookup/registration before treating a shared brush field as a usable bridge.

The asset loader remains an independent lead, not a ready test. Asset-load dispatch 2b5e04 selects 1b1ff8 / 1b2030 / 1b2014, which delegate through 1abd0a / 1abca0 / 1abc36. The startup loader 17caf4 initializes NOR/NAND resources; 182518 invokes it during initialization. A nearby “Loading RAM Asset” string alone proves no external image-upload command. Do not send arbitrary asset pointers or overwrite factory assets based on it.

## Next car batch

The previously prepared [diagnostic-surface tests](HUD-DIAGNOSTIC-SURFACE-TEST-2026-11-20.md) remain the executable larger-surface activation probes: dim RGB and factory grid/circles, each bounded to 30 seconds with explicit stop handling. Neither is an uploaded custom-image test. No strip, Hz or alignment rerun has been added.

The new marker remains offline-only (`live_drawing_allowed: false`, no resource ID/endpoint) until external destination binding, owned allocation/removal, current-version compatibility and recovery are demonstrated. Preserve V1 and keep its stopped/running state separate from file preservation: the owner deferred runtime restoration after the previous car session.

## Follow-through: concrete named-asset provider

The ARM DefaultAssetProvider constructor at 0x2e88c0 installs vtable 0xaacc04 at object+0x1c. Its slot+0x6c is 0x2e85b4; slot+0x74 is 0x2e85bc, matching the full-size widget's call convention. The application constructor calls singleton getter 0x2e9afc and stores its result at application+0x40 (0x1ab71c..0x1ab726). This identifies a concrete provider implementation, not a live observation of the widget's manager pointer on installed008.

The getter delegates to 0x2f7f78 using a typed-provider subobject at +0x7c. That code performs a named-tree lookup (0x2efb80 → 0x2edfe0) at provider+0x80. The matching name returns the cached bitmap. The subsequent `(name, 0)` operation removes the cache node, returns the bitmap pointer, and does not destroy that bitmap. Its cache-miss path calls asset resolution at 0x2e42e0 and builder 0x2ebc50; these are further tracing targets, not Ethernet commands.

`tools/verify_hud_asset_provider.py --image <004-main> --output <report.json>` now executes the actual getter, string lookup, singleton getter and tree removal. A synthetic one-node cache is returned and removed, and the opaque bitmap bytes remain intact. Only mutex operations and node deallocation are intercepted; singleton initialization flags are preset. No actual bitmap construction, cache-miss resolution, rendering or externally reachable insertion is claimed. The synthetic cache experiment does not grant a way to write this tree from the car's Ethernet interface.

The next car batch remains two distinct, unrun full-surface activation tests. Both are ready with the existing runner and cleanup procedure. Their exact purpose and observations are in [the next-trip card](HUD-NEXT-TRIP-CARD-2026-11-20.md). This trip is not a request to repeat the uploaded strip marker.
