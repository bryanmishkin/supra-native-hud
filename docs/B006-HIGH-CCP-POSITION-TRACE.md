# Native high-CCP picture-position control

19 November 2026. Offline trace; no vehicle operation or V1 change.

A separate receiver-facing position model exists beyond the tested detailed intersection and roundabout models. It is **model type 30**, sent through B006 maneuver-control method 9, union tag 4. This is not evidence that it routes the existing PiP stream to the windshield.

## Exact sender contract

`SetHighCCPPicturePosition4ICHUD` is staged around controller `0xaa0580`. Its logic setter `0xa42e7c` copies a center-position vector, a bitmap-resource identity and an unsigned orientation. Constructor `0xd41fd8` explicitly sets model type 30. Sender `0xab50b8` converts the resource identity, copies the center coordinates, and uses `0xab00dc` to construct control tag 4 before the maneuver-control send path `0xab4ec8`.

The captured native serializer `0xbb57f8` emits this 15-byte member payload:

| Member | Wire encoding |
| --- | --- |
| Model ID | big-endian u32 |
| Model type | u8, 30 |
| Center X, center Y | two big-endian u16 values, no vector-length prefix |
| CCP bitmap resource ID | big-endian u32 |
| Orientation | big-endian u16 |

`tools/verify_high_ccp_position_native.py` executes the actual serializer and nested scalar/vector writers. Only stream snapshot/write boundaries are supplied. Three synthetic identities reproduce the expected bytes exactly. Synthetic coordinate values do not establish physical units, scaling, clipping, orientation units, receiver acceptance or ownership.

## Resource family matters

The native setter calls `0xa42bac` on its embedded image input. That function constructs the resource through `0xa42b74`; the constructor passes literal **resource type 1** to base constructor `0xa426dc`, then copies image bytes. This is the bitmap family, not PiP type 2. Although the serializer can mechanically encode a type-2-shaped numeric ID, no native binding of a PiP stream through this model has been established.

The retained configuration advertises two model-30 slots starting at `0x1e000000`. The parent corpus audit found no type-30 update in the retained recordings. Advertised capacity is not permission to overwrite shared model slots or proof of a visible placement.

## Distinct from detailed intersection model 7

The tested type-7/tag-6 model is the native `sendIntersectionHighElement` shape. Its picture field remains a direct `highGuidingPictureID`. Its final field is the `maneuverHighLinkListID`, checked against model type 31 by the sender at `0xab4810` and converted at `0xab484c`. That final field must not be relabeled as a type-30 picture-position reference.

Type 30 is independently sent through the control channel. No direct type-7 reference to it was found in this sender path. It is a concrete separate bitmap-position lead, not a repair to the previously tested PiP descriptor.

## Remaining evidence needed before execution

Identify the receiver's intended center-coordinate domain and which control instance maps to each output; determine shared-model admission, exact withdrawal and restoration; and establish that the selected bitmap encoding is accepted by this path. Until then, keep this as an offline codec/native-proof result. Do not fill unexplained fields or send a PiP ID merely because both are u32 values.

## ICHUD staging does not supply a normal image

Deeper tracing limits the apparent bitmap opportunity. The ICHUD job at `0xaa0398` reads center coordinates from the first two u16 values of its position chunk. It constructs the embedded image using `0xa48a24`/`0xa489f0`: image ID starts as `0xffffffff`, dimensions start empty. It appends only the low byte of the chunk word at +4 to that image's data vector (`0xaa0468`–`0xaa047c`), copies the image into job +0x184 and explicitly sets orientation to zero at `0xaa04a4`. The reviewed path does not replace the absent image ID or populate dimensions with the 277×160 PiP geometry.

Thus the common setter can stage bitmap-family resources, but this actual ICHUD caller is not evidence of a custom-pixel upload. It may be a position/control update associated with independently published imagery; that association remains to be traced. Do not infer a working custom bitmap from the setter name alone.

The offline codec `tools/b006_ccp_position.py` now encodes/decodes the exact 32-byte method-body shape and can replace only its picture reference with absent. Three tests cover the native payload vector, byte-local reference withdrawal and malformed identity/extent rejection. `without_picture` is deliberately not called verified cleanup: a zero/default control model, model disposal, or restoration behavior has not been observed or executed for this type. A shared model cannot be overwritten merely because no update appeared in the saved interval. These gaps keep the type-30 path from being an executable car-test candidate today.

## Native position source and publication order

NavigationFully `0x87d958` emits chunk70004: two u16 coordinates from item+0x10/+0x12, followed by the u32 picture counter read from render-context+0x54. That is the same counter used by native pixel metadata. The one-byte ICHUD staging value is therefore derived from this counter; do not dismiss it as arbitrary padding.

The position setter `0x87d948` has one direct caller, `0x7f45f4`. The caller combines a projected point with signed16 element fields+6/+8: `x = projectedX + field6`, `y = field8 − projectedY`, converts to unsigned32 and truncates to unsigned16. The physical meanings of those element fields and the projection's actual selected-view values remain to be confirmed. A generic midpoint cannot be substituted on this evidence.

Controller `0xaa0740` first parses position data at `0xaa0394` and, when present, calls `SetHighCCPPicturePosition4ICHUD` through `0xaa0580`. It then independently parses HG PiP data at `0xa9ff88` and calls `SetPiPElement4ICHUD` through `0xaa06b8`. The subsequent attachment path proceeds when either position or PiP changed; the HU sender does not require both to be present. Receiver association of the position counter/control with incoming pixels still needs its special-resource conversion path. This ordering is new concrete evidence, not a conclusion that position is unnecessary to physical output.
