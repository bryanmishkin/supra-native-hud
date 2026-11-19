# B00E advertised configurations and candidate canvases

Offline analysis, 2026-11-19. No vehicle commands, installed V1 changes, commits, or pushes.

## Confirmed captured advertisement

Strict parsing of the retained create-instance replies finds 14 successful replies, each with an identical 360-byte body and handle 100. See configs.json and decode_configs.py. The bitmap configuration (variant 33) advertises resource type 1, ten resources starting at 0x01000000, maximum bitmap resolution 128 × 128, and RLE32 enabled; RLE24, PNG and JPEG are disabled. This is a resource limit in this instance's reply, **not evidence of a 128 × 128 visible windshield canvas**.

The reply also advertises ListCarousel configuration variant 15/type 0x1c, one resource at 0x1c000000, with trailing bytes `0080008004001e`. VoiceRecState variant 16/type 0x2f has one resource at 0x2f000000 and tail `0000000004001e`. The former contains a 128/128 pair in the shared RicDimension structure (see the follow-up trace below), but visible-area semantics remain unproven; the latter's zero pair must not be interpreted as absence of voice graphics.

List model configurations present: Entertainment type 0x16, RadioTune 0x30, Notification 0x19, Popup 0x1a, InCall 0x17, UnifiedCall 0x2d. Also present: text type 3 (100 resources, base 0x03000000), composite text type 10 (eight resources, base 0x0a000000), generic resource type 7, model types 0x13 and 0x2c. No PiP configuration variant 35 appears in this reply.

## Captured HMI serializer evidence

HmiMain3D SHA256 `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`. The ELF's exported CommonTypes vtable symbols identify these structures and virtual function addresses:

| Structure | Vtable VA | Serialization-shaped function pair |
| --- | --- | --- |
| ListCarouselConfigStruct | 0x31a52c8 | 0x2921464 / 0x29214a4 |
| VoiceRecStateConfigStruct | 0x31a4028 | 0x2924710 / 0x2924720 |
| BitmapConfigStruct | 0x31a2df8 | 0x2925358 / 0x291fda0 |

ListCarousel function 0x2921464 processes nested objects at +4 and +0x1c through 0xf87380, then fields at +0x2c through 0x2719b34 and +0x2e through 0x2719b48. Its paired function uses corresponding helpers 0xf87334, 0x2719b0c, 0x2719b20. BitmapConfig 0x2925358 similarly processes nested objects at +4/+0x1c, then four fields at +0x2c/+0x30/+0x34/+0x38 through 0x2925158. VoiceRecStateConfig 0x2924710 delegates its nested object at +4 to 0xf87380, without Carousel's additional fields. These are concrete starting addresses for field tracing, not yet semantic proof that Carousel's nested object is a windshield rectangle.

The exact static disassembly is retained in carousel-vfunctions.json, voice-vfunctions.json, bitmap-vfunctions.json. Naive direct string-pointer and MOVW/MOVT references produced no useful hits; their empty outputs do not disprove code reachability.

## What this does and does not establish

B00E has an actual advertised RLE32 bitmap capability larger in height than V1's known 150 × 36 B006 image. The retained create reply does not tell us which model fields bind that bitmap, where a model will render, whether its geometry is clipped/scaled, or whether bitmap IDs in the shared instance are available to us. Parent's separate scan reports only text/composite-text uploads in retained B00E traffic, so it supplies no factory bitmap-binding example.

Next bounded offline step: trace the nested config serializers above and model serializer fields for Entertainment, UnifiedCall, VoiceRec and Carousel; distinguish resource IDs from enums/system-icon selectors. A distinctive IU trident image should be used only once the applicable bitmap-reference field, collision-safe resource allocation, and exact removal path are established. A successful upload or advertised size alone is not the larger-display proof.


## Follow-up: the common dimension structure is identified

The captured HMI supplies stronger type evidence than two matching numbers:

- The exported `RicDimensionStruct` vtable is at `0x31a4b90`; its object vtable pointer is `0x31a4b98`.
- ListCarouselConfig construction at `0x2837830` loads its own vtable and places `0x31a4b98` at object offset `+0x1c` (instructions `0x2837870` / `0x2837874`). The resulting object is read at `0x2837878`.
- BitmapConfig construction at `0x28381e4` places the **same dimension vtable** at object `+0x1c` (`0x2838224` / `0x2838228`; object begins at stack+4).
- RicDimension's read function `0x294b894` delegates its member at `+4` to `0x27f6980`. That helper reads 16-bit elements and appends them to a vector. Its write function `0x2927318` delegates to `0x27f3544`, which computes the element count by dividing the vector byte span by two and writes each 16-bit element.

Therefore Carousel's 128/128 advertisement is carried by the same dimension type as the BitmapConfig maximum-resolution advertisement. This narrows the geometry lead materially. It still does not supply a screen origin, windshield destination, scaling rule, or proof that a Carousel model is shown in the windshield. RicDimension is a vector, not a hard-coded two-coordinate C++ structure; never infer a universal two-element wire format solely from this native object layout.

The HMI config dispatch constructs VoiceRecStateConfig as a wrapper around a CarouselConfig (`0x28378d4` onward), explaining why the voice configuration can inherit similar trailing fields despite its own serializer merely delegating the nested object. Zero dimensions remain an advertised property, not evidence that factory voice graphics have zero visible area.

## Candidate experiment matrix and admission limits

These are candidates for the parent test planner, not authorization to send incomplete models:

| Candidate | Bounded asset | What a successful visual observation would establish | Remaining gate |
| --- | --- | --- | --- |
| Known-working B006 control | 150 × 36 IU trident or distinctive control, same proven path | Asset/color/observation pipeline works in the existing strip | Use existing collision-safe allocation and cleanup; pause V1 |
| B00E Carousel image item | Start 32 × 32 or 64 × 64; maximum advertised bitmap 128 × 128 | Whether the candidate model binds our bitmap and which display renders it | Exact image field, model selection/focus, own-resource allocation, cleanup |
| B00E Carousel size ladder | 32, 64, 96, 128 square, one at a time | Actual clipping/scaling and visible boundaries if image binding first succeeds | Do not jump to this until the smallest marker is visible and removal verified |
| Entertainment/radio image-bearing item | At most 128 × 128 resource; do not assume radio popup size | Whether this distinct item type accepts a custom image | Its exact typed image field; factory text/metadata captures alone are insufficient |
| UnifiedCall/phone item | No supported custom-image geometry yet established | Potentially a separate item binding if proven offline | No image injection candidate ready from current canvas evidence |
| Voice state | No supported custom-image geometry yet established | Factory voice transition only is currently proven | Do not substitute bitmap IDs for state enums |

For every new model candidate, record windshield and cluster separately, leave a full 30-second observation window, remove model references before deleting only our image resources, and require normal display plus resource-absence evidence before continuing. No arbitrary IDs, oversized images, or factory-resource deletion follows from the 128 × 128 advertisement. Installed V1 and startup remain unchanged.
