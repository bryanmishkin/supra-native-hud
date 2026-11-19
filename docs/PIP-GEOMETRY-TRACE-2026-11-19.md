# PiP geometry and native descriptor trace

Offline continuation, 19 November 2026. V1 and the vehicle are unchanged. No Hz tests or vehicle connections. This replaces the assumption that a known 320×200 image needs a known 460×237 resize with traced geometry domains.

## 320×200 is our marker choice, not factory geometry

`tools/pip_trial.py:allocation` selects width320/height200 after checking the returned resource capacity. The native marker profile repeats that choice. These values were not measured from a working Supra native video stream.

The retained B009 selection reports scale1,460×237,selection1/Kombi. It is a receiver selection, not an observed 460×237 pixel upload or a full windshield allocation. The reference G30 uses yet another content size620×313 and registers an800×480 PiP backing. It therefore does not establish one universal equality between PiP descriptor dimensions, native backing and selected visible geometry.

## Returned capacity rechecked across the corpus

All17 parsed successful B006 create replies in the previously audited46-unique-PCAP corpus have the same complete body hash and the same PiP configuration: handle200, count5, resource base0x02000000,320×320, depth limit1, packaging limit0. The single complete response-body SHA-256 is recorded in the private `create-configs.json`. All 17 parsed create requests use `BMW.IC.Guidance / ICGuidanceControl / BMW`, version3,3,1. All observed reply client fields are1; identity strings alone do not establish which process initiated each request.

Unparsed streams and the earlier continuity exclusion remain excluded. No new capacity or dynamic resize notification was established. The capacity cannot be expanded merely because B009 selected a larger visible width.

## Native controller dimensions check

Captured controller SHA-256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`:

- `sendPIPElementResource` at0xab3b40 calls0xaae1a8.
- For resource type2,0xaae1a8 selects the dimension vector in configuration+0x8c and calls0xaae078.
- 0xaae078 compares width and height independently with the supplied maxima. An oversized dimension invokes the diagnostic logger, then returns. It does not resize, crop or overwrite the dimension vector.
- The subsequent native send path copies the dimension elements, then serializes the resource.

`tools/verify_pip_dimension_check.py` executes the type selector, comparison and actual native vector accessor on eight size pairs. Only the diagnostic logger is intercepted. The test checks that the entire synthetic object/config/vector region is byte-identical afterward. Sizes460×237 and800×480 produce the expected overflow diagnostic;320×200 and320×320 do not. Zero dimensions also do not trigger this *particular upper-limit check*; that is not a claim that zero is a usable receiver image.

## Native PiP serializer

Captured HMI SHA-256 `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`, native serializer0x289e7bc:

`tools/verify_pip_native_wire.py` executes the serializer and underlying native integer/vector/enum writers. Only stream snapshot and byte-write ABI operations are supplied. For320×200,320×320,460×237 and800×480, the output is exactly `u32 resource ID, u8 type, u16 width, u16 height, u8 depth, u8 packing`, big-endian. There is no dimension-array length and no image byte array in this descriptor. The old PiP encoder matches this format.

This rules out a hidden resize or an extra dimension-length prefix in these inspected HU stages. It does not prove the receiver accepts an over-capacity descriptor, nor validate packaging1 on the Supra.

## Producer viewport

NavigationFully0x7ee4c4–0x7ee4e4 calculates width=right−left and height=bottom−top from context+0x58..0x5e. Setter0x87c774 puts those values directly into PiPInfoItem+0x12/+0x14. Executed rectangles preserve460×237 and320×200 unchanged, including a nonzero-origin rectangle.

CGVView's virtual rectangle setter0x61e374 forwards to0x7de314, which copies exactly8bytes into that context. The adjacent84-byte metadata block carries identity/flags; this producer does not write width/height into it. The serializer, native viewport and receiver-selected visible geometry must therefore remain separate until their actual attachment path is traced.

## Reproduce

With the existing analysis environment containing Unicorn and pyelftools:

```
python tools/verify_pip_dimension_check.py /private/NavNBTEvoController
python tools/verify_pip_native_wire.py /private/HmiMain3D
```

Both tools reject mismatched binary hashes. No OEM binary is embedded or published. No live runner is enabled by these checks. The native DisplaySink transport remains separately implemented and tested; combining it with an arbitrary resize is not a verified receiver binding.

## Retained producer commands decoded

The existing shared-memory snapshots contain six distinct full-buffer hashes across52 matching file copies. The first HGPictureInPicture chunk (`0x70008`,12-byte payload) decodes as `<BBHHBBI`: maneuver type,resource type,width,height,depth,packing,pictureID. Its nonzero geometries are800×480 and480×431, both depth0/packing1, with picture IDs2/3. Two distinct initial snapshots contain0×0/picture1. All six snapshots carry sequence`0xfffffffe` (reusable). They are retained producer bytes, **not active-frame or windshield evidence**. Directory phase labels do not establish the time those bytes were drawn. Runtime displayable IDs9/11 cannot be assigned a physical display merely from matching dimensions.

`tools/audit_gv_pip_geometry.py` decodes only the first bounded chunk, ignores trailing stale memory, requires the exact payload length, and keeps active-frame and destination proof false. Five regression tests cover truncation, extra payload, stale trailing chunks and sequence interpretation.

Native construction independently establishes an800×480 type0 display session (userID0x321,caption1056), stored in the manager's IC slot+0x70. The displayable constructor copies `(0,0,width,height)` into its rectangle; type0 attachment forwards that rectangle to the view. This supports a producer-side800×480 backing. It does not establish an800×480 windshield allocation or override the advertised320×320 resource capacity.

## Resource checks correlated with packets

`tools/audit_pip_checks.py` pairs requests/replies on exact reversed TCP endpoints plus client/session IDs. Duplicate transaction keys remain ambiguous. It recovers only a validated complete prefix before an explicitly truncated final message, never scans for a plausible next header.

Across46 unique captures, there are nine PiP-type resource checks, all client`0x5350`,handle200,resource`0x02000004`. They form absent→present→absent sequences in three recording views (two views record the same first attempt). These are **our tests**, not factory checks. Two previously truncated streams contribute validated prefixes of740690 and852808 bytes; neither adds factory PiP checks. One TCP-gap capture remains excluded. Scanning all78 local PCAP paths finds no additional unique usable capture beyond this corpus.

Consequently our descriptor became present and was removed, while the observer reported only a turn arrow. A positive existence response therefore does not establish attached pixels or windshield output. The packet corpus does **not** demonstrate that an existing factory resource suppressed its PiP upload.

## Dedicated ICHUD publication path

The captured controller has separate generic and ICHUD PiP paths. The HG metadata job reads its parsed chunk vector+0x94 and sends `SetPiPElement4ICHUD` at0xaa06b8. Logic stores this in model+0x1018; generic PiP uses+0x1318 instead. The ICHUD resource sender reads+0x1018 when selector+0x15c is zero.

The native IC configuration defaults to existence-check-before-upload; HMI defaults to immediate upload. The response handler requests upload only when existence is false. This is a verified native mechanism, **not an observed explanation for our failed tests**, because no factory PiP checks were found.

Publication additionally requires a connected sender and a nonempty dedicated model-change vector. Retained HG bytes alone prove neither condition. The next binding trace follows that publication and receiver selection rather than assuming descriptor registration creates a pixel surface. The retired live runner remains retired; V1 and its installer remain unchanged.

The dedicated job stages `SetPiPElement4ICHUD` before notifying attachment/switch. Those notifications require a nonzero guidance-session identity and pending attach/switch flags. Native publication at0xa8b588 requires connected byte+0xf8 and, for ICHUD, a nonempty change-vector+0x1cc before dispatching0xa89bf4. Thus registration, publication and attachment are separate obligations.

HG pictureID is the resource's original identity. IC conversion0xaacac4 allocates a converted identity from the model's PiP pool+0x1330, stores it at resource+0x14, and records its association with the original identity. There is no demonstrated `base+pictureID` formula. This is a controller-local association; the inspected B006 descriptor carries the converted resource identity, not an extra original-picture field.

The render context picture counter itself does increment: CGVView0x61e384 loads this+0xa8, adds1 and calls0x7de30c. This is render-context+0x54, also used by HG and metadata. Therefore incrementing the old marker's picture value is not, by itself, a demonstrated fault; exact update cadence and receiver association still require tracing.

## Attachment identity is not the B006 handle

The attach observer0xa9f094 emits `[maneuverID,guidanceSessionID]`. Manager handler0xa7644c uses that session and current maneuver to request attachment through its IC display session. The command-job status handler accepts only the matching outstanding notification object before copying the returned guidance-session identity. B006 handle200 is not that identity.

Observer construction0xaa0120/0xaa00c8 and registration0xa9f59c use an existing in-process maneuver object pointer and typed-event interface. No standalone SOME/IP CreateSession operation is established by this trace. Hardcoding a captured session number or sending an invented attach packet would skip the actual owner/correlation contract. The available native DisplaySink handshake cannot by itself manufacture that object or session.

Native publication verification (`tools/verify_pip_publication_gate.py`) executes all four connected/nonempty combinations. Only connected plus nonempty dedicated changes dispatches publication. The other three release the event. The native vector helper executes unchanged; the tool stops before downstream dispatch/release rather than substituting their behavior. See [attachment ownership](PIP-ATTACH-OWNERSHIP-2026-11-19.md) for the exact internal observer, session and dynamic identity allocation.
