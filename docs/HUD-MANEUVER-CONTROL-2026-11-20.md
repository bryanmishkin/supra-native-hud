# Maneuver control: complete union and image-target encoding

This is an offline producer contract, not a windshield resize command. No vehicle operations or V1 changes occurred. The completed strip and Hz tests remain excluded from the next batch.

## Complete method-9 union

The earlier four-member inventory stopped before the final dispatch fallback. The captured controller implements five members:

| Tag | Native sender meaning | Union constructor | Member writer |
| --- | --- | --- | --- |
| 1 | CCPInfo | `0xab013c` | `0xbbec7c` |
| 2 | ManeuverListState | `0xab01c8` | `0xbb07d8` |
| 3 | HighCCP | `0xab0168` | `0xbbf46c` |
| 4 | HighCCPPicturePosition | `0xab00dc` | `0xbb57f8` |
| 5 | HighGuidingImageInfo | `0xaafc80` | `0xbb0aac` |

The dispatch chain is `0xbbf580 → 0xbbf548 → 0xbbf510 → 0xbb589c → 0xbb0b50`. The final function accepts tag5 and otherwise returns zero. The high-image-info sender at `0xab4f80` constructs tag5 and uses the same method9 send path `0xab4ec8`.

## Image-target information is not a rectangle

`tools/verify_high_image_info_wire.py` executes the captured writer and its nested scalar/enum writers. All sixteen combinations of the two valid 0..3 enum ranges reproduce this exact 15-byte member payload:

| Field | Encoding |
| --- | --- |
| Model ID | big-endian u32 |
| Model type, 50 | u8 |
| Render instance | big-endian u32 |
| Referred maneuver ID | big-endian u32 |
| Image target | u8 enum |
| Image content type | u8 enum |

Only stream snapshot/write imports are supplied; the actual captured writer runs. Source model fields+0x14/+0x18/+0x1c/+0x20 are copied at `0xab4fec–0xab5010`, and the native log at `0xab504c` supplies their names. The tuple contains neither pixel data nor x/y/width/height. The separate [native receiving-backend trace](HMI-RIC-RECEIVING-BACKEND.md) now resolves the target names: NONE, HMI_ROADBOOK_SPLITSCREEN, HMI_ROADBOOK_PAD, and HMI_GUIDING_LABELS_MAP. These are not B009 windshield/cluster selections. The prior 43-configuration audit advertised no model50 capacity; this test does not override that admission constraint.

## HighCCP trailing values are guidance angles

The tag3 caller at `0xab74f4` reaches constructor `0xab0168` through `0xab76f4`. Its native logging names the trailing values `nextManeuverDirectionAngle`, `routeDirectonAngle`, and `nextDestinationDirectionAngle`. The source u16 fields+0x7c/+0x7e/+0x80 are staged at stack+0x114/+0x116/+0x118. The nested writer emits them through `0xbbef74`, `0xbbf004`, and `0xbbf094` using the u16 writer. They must not be reinterpreted as viewport dimensions because they happen to be adjacent integers.

## Reproduction and limit

Run `python tools/verify_high_image_info_wire.py /private/path/NavNBTEvoController` with the analysis environment's Unicorn and pyelftools dependencies. It requires controller SHA-256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a` and refuses another binary.

This closes a missing producer-union branch, but does not establish a receiver clip setter, a supported model50 slot, or a larger windshield surface. Do not schedule a car trial from this encoding alone. Continue at the receiving implementation/output owner and reconcile it with the actual cluster address and positive windshield traffic.
