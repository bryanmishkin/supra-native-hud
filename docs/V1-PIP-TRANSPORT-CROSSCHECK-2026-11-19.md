# Working V1 versus larger-image transport

Offline packet audit, 19 November 2026. No vehicle connection or V1 change.

## Measured comparison

`tools/audit_image_transports.py` deduplicated 48 capture hashes. One capture was excluded by strict extraction. Streams without valid framing were excluded; explicitly truncated endings contributed only validated complete prefixes. Counts below are captured occurrences, not unique render events: independent recordings can overlap.

| Path | Client | Resource / variant | Dimensions | Upload occurrences | Inline image bytes |
|---|---|---|---|---:|---:|
| V1 bitmap | 0x5348 | 1 / 2 | 150×36 | 6,777 | 22,434,592 |
| Experimental PiP | 0x5350 | 2 / 3 | 320×200 | 3 | 0 |

The V1 resources are 0x01000008 and 0x01000009. The PiP resource is 0x02000004. Another 49 factory type3/variant4 resources were observed; this audit does not decode their payload and makes no pixel-content claim about them.

## What this establishes

V1 puts encoded image bytes inside B006 method3. Its road-icon model references that same bitmap identity; the working app alternates its two resources and verifies removal. The PiP descriptor instead carries an identity, dimensions, depth and packing. Its eleven-byte payload contains no image array. Native serializer execution independently established that this is the expected descriptor structure, not a missing field in our encoder.

Consequently PiP resource existence plus a visible maneuver arrow is not proof of a pixel attachment. The separate producer-to-receiver pixel path must succeed too. The audit does not determine which specific attachment step failed, and cannot exclude errors in the separate producer's pixel format.

## Geometry domains must remain distinct

- 150×36: negotiated bitmap capacity and actual successful V1 upload dimensions.
- 320×320: returned PiP resource capacity.
- 320×200: our failed test's selected image dimensions, not measured factory content.
- 460×237: captured B009 selection, destination enum1/Kombi; not a windshield grant.
- 800×480: native producer backing and selected style header coordinates.
- 277×160: selected HUD PiP junction/intersection element extent in the captured style database.

No equality or automatic scaling between these domains has been established. Making the V1 upload larger or appending RLE bytes to a PiP descriptor is not a supported fix.

## What the working path lets us isolate

Use the same recognizable marker for both paths. V1 supplies the positive control for custom pixels and windshield visibility. For PiP, independently establish (1) producer buffer content, (2) transport selection/lease, (3) picture identity association, (4) model selection and visibility, and (5) removal. A positive result at any one stage must not be reported as success of the next.

The source-side factory job/attachment sequence is an alternative producer implementation. Our standalone Screen producer bypasses that job chain; failure to reproduce the job chain is therefore not by itself the cause of the failed Screen tests. The outstanding receiver-side pixel association remains the critical distinction.

The radio frame and height-adjustment corners demonstrate factory-drawn geometry. They do not establish writable pixel interiors or dimensions of a custom image allocation. No new car test is enabled by this audit; no Hz work was added.

## Reproduce

Run `python3 tools/audit_image_transports.py /private/capture-root --output /private/image-transports.json`. The private report retains source hashes, flow/offset evidence and exclusions. Do not publish the report or captures without reviewing vehicle/private data.
