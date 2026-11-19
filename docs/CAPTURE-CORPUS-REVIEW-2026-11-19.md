# Saved-capture coverage and PiP attachment review

19 November 2026. Offline review only. Installed V1, worker, supervisor, startup and rollback packages are unchanged. No new car session or Hz test is requested.

## Coverage actually checked

- Enumerated 157 local ZIP archives and loose PCAP files: 48 distinct PCAP hashes; no archive-only PCAP hash. One capture fails strict extraction. Invalid streams stay excluded; only explicit truncated endings permit validated complete prefixes.
- Across those PCAPs, eight decoded B009 selections all carry scale1,460×237,destination1. Independent captures may overlap; eight is not asserted to mean eight distinct real-world transitions.
- Examined 114,716 retained `.bin` file paths with bounded, whole-file SOME/IP framing. 28,077 unique file hashes passed framing. These include extracted recordings and test artifacts, not exclusively live data. All 14 decoded B009 messages (selection/completion) agree with destination1; no different destination was recovered there.
- Rechecked 198 GV command snapshots: 52 PiP-containing file copies, six distinct snapshot hashes. Nonzero PiP geometry remains800×480 or480×431,depth0,packing1. Their reusable sequence markers do not prove an active frame or physical output.
- Indexed 33 distinct fault-record hashes, preserving their capture provenance and embedded worker result. These are records across historical versions, not 33 current-build failures or even necessarily 33 distinct incidents.
- Google Drive root inventory contains101 relevant ZIP entries.82 match a local filename and size;18 have same-size local candidates under different names (including a duplicate upload). These are metadata comparisons, not remote-content hash verification.
- Retrieved the remaining original96,850,653-byte diagnostic archive from Drive. Of22,602 members,22,586 match the corresponding local file byte-for-byte. The16 differences are historical source, reports and manifests. No missing raw capture was found in that archive.

The private reports retain file hashes, paths, exclusions and original archive member inventory. Do not equate first-level protocol decoding with completion of firmware reverse engineering, or claim all Drive folders/media have been exhaustively reviewed.

## What the data says about the missing pixels

The working bitmap path and unsuccessful PiP path are different transports. The earlier cross-check found V1 inline RLE bitmap data in type1/variant2 uploads. PiP type2/variant3 contains an11-byte descriptor and no image bytes. The wider standalone-file scan confirms the same dimensions and resource families; it adds no observed larger inline bitmap path.

Our failed native marker never subscribed to B009. The reference starts that negotiation before Guidance, but its destination1 is cluster video and destination0 pauses that implementation. The captured Supra factory selections are destination1 too. A windshield turn arrow produced by the structured guidance model is therefore not evidence that the native video stream reached the windshield.

The native output driver submits images to local physical video hardware. The retained source establishes RGBA-over-RGB output packing. The cluster's advertised resource has packing limit0, while retained factory producer chunks carry packing1; this discrepancy remains a producer/capability question, not permission to override the receiver limit. It must not be hidden by reporting both as the same successful image format.

The selected style database's277×160 HUD PiP element is geometry in the factory renderer. Its800×480 header is not a granted windshield canvas. Neither can be substituted for the460×237 destination1 selection or320×320 advertised resource limit.

## Findings that prevent another misleading test

1. Descriptor registration/existence is already known to succeed. Repeating it cannot establish pixel delivery.
2. The captured factory cluster negotiation cannot be relabeled as HUD routing.
3. An empty radio frame or height-adjustment corners are factory geometry, not evidence that their interiors accept an app bitmap.
4. Native Screen posting and its local cleanup are separate from remote picture attachment and removal.
5. A source-side guidance job/session is not the receiver. The standalone producer bypasses those factory jobs, so their absence alone is not a diagnosed cause.

The larger-display attachment is **not fixed by this review**. The retained artifacts have now been cross-checked more broadly rather than assuming an unexamined archive contains the missing binding. The failed live runner remains retired. This commit adds reproducible offline auditing only; it does not advertise a new live candidate.

## Reproduce

```
python3 tools/audit_saved_capture_coverage.py /private/outputs /private/coverage.json
python3 tools/audit_saved_someip_bins.py /private/outputs /private/standalone-bins.json
python3 tools/audit_gv_pip_geometry.py /private/outputs > /private/gv-buffers.json
```

`audit_saved_capture_coverage.py` records partial/rejected streams explicitly. It does not resynchronize arbitrary bytes. `audit_saved_someip_bins.py` requires complete whole-file framing; its accepted files may contain synthetic fixtures and its counts must not be summed with PCAP events.

See [working-path comparison](V1-PIP-TRANSPORT-CROSSCHECK-2026-11-19.md), [source/receiver distinction](PIP-SINK-CONTRACT-GAP-2026-11-18.md), [selected style evidence](SELECTED-STYLE-RENDERING-2026-11-19.md), and [native driver](OUTPUT-DRIVER-TRACE-2026-11-18.md).
