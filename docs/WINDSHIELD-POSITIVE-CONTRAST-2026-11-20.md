# Positive windshield comparison against cluster-only output

20 November, offline. V1 unchanged. This compares the actual saved requests from the numbered-image car session, not freshly generated candidates.

## The controlled difference is now exact

Both two-image runs contain **89 saved requests**. After removing only the SOME/IP envelope from the comparison, **88 request methods and bodies are identical**. The only changed request is013, B006 method14, model40 (RoadInfo), variant2.

Both bitmap uploads are byte-for-byte identical between the runs, including their IDs, type1,150x36 dimensions and compressed pixel data. The same two images are therefore supplied to the same resource space. The complete17-command setup/withdrawal sequence differs only in the populated road-list body. Cleanup passed in both saved result journals.

| Actual supplied RoadInfo structure | Windshield observation | Cluster observation |
| --- | --- | --- |
| One entry containing image1 and image2 | No numbered image | Both numbered images, side-by-side |
| Two entries, each containing one image | Both numbered images, second clipped | Both numbered images, side-by-side |

The second structure changes entry boundaries and their encoded array lengths. Handle, model identity, road type, alignment and entry trailing-byte values remain the same. It does not change image size, pixel encoding, color, bitmap identity or a MapCanvas rectangle.

The visual evidence comes from owner observations and photographs; it is not inferred from successful replies. The single-image control additionally shows the exact same image1 upload in the windshield.

**Supported conclusion:** the already-working inline pixel path reaches the windshield through the receiver's RoadInfo structure/layout handling. These records isolate an entry-structure difference in the supplied requests that accompanies the visible-output difference. Encoding failure cannot explain the contrast because the uploaded bytes are identical.

**Not yet distinguished:** a per-entry aggregate-width limit, a one-image-per-entry rule, or another receiver layout predicate. The saved traffic does not expose that internal predicate. It also does not isolate every pre-existing receiver state or unrelated factory message; these are direct request journals, not a claim of complete bus-level causal isolation.

## Contrast with the actual PiP capture

The retained cluster-only PiP capture parses without stream errors. Its resource upload is type2/variant3: an **11-byte descriptor**, dimensions277x160, depth0, packaging0, with **no inline pixel array**. B009 then reports destination1,460x237. The actual custom pixels use the separate producer path. The windshield shows the stock maneuver symbol while the cluster shows our custom image.

This is different from the successful type1/variant2 inline bitmap attached to RoadInfo. A shared B006 endpoint or accepted resource ID does not make these pixel transports or their attachment rules interchangeable.

## What the comparison says about MapCanvas

The positive windshield request sequence does not include the local DNAVIMapCanvas method0x24 operation traced in NavigationBasic. That local operation is a separate IPC contract, not a B006 method with matching numeric values. The successful requests establish the RoadInfo link; they do not by themselves prove that resizing a local map window changes the RoadInfo parent's windshield boundaries.

The boundary investigation should therefore follow the receiver's RoadInfo layout and its parent clip, using these exact positive/negative inputs as constraints. Any proposed root-window linkage must account for why identical image bytes disappear when grouped in one entry and reappear when split, without treating the captured cluster-only PiP path as a positive windshield reference.

## Reproduction

```sh
python3 tools/compare_windshield_positive.py /absolute/private/road-session /absolute/private/road-comparison.json
```

The tool validates request envelopes, decodes actual uploaded resource and road-list bodies, preserves request hashes, compares every saved request method/body, and reports cleanup separately from visual observations. It has no network operations. Private evidence also retains the PiP packet hash, flow, stream offset, timestamp and decoded selection; addresses and proprietary packet bodies stay out of Git.
