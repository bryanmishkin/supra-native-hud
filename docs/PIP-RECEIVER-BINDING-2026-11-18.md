# Receiver binding: what the failed tests actually establish

Status: offline investigation, **not a repaired or ready-to-run candidate**. V1 remains unchanged. Both marker attempts produced a turn arrow but no custom pixels. The cause is not yet isolated; do not describe any one of the remaining possibilities as the diagnosis.

## New bounded execution evidence

`tools/verify_pip_binding_records.py` executes retained ARM instructions in Unicorn, gated by the exact SHA-256 identities below. It contacts no vehicle and embeds no factory binary. This is producer-side verification, not cluster emulation.

- NavigationFully initializer `0x87ba68..0x87bad4` clears exactly 84 bytes, with adjacent sentinels preserved. Its construction pattern is individually initialized bytes/halfwords through offset 19, a 60-byte region at 20..79, and a final word at 80. The length alone is **not evidence for five resource-slot records**.
- Both captured maneuver producers (`0x7ee598` and `0x7f6464`) load the maneuver object's `+0x200` value and put it at record offset 16. Six execution cases, including IDs `0x0f000000` and `0x0f000004`, write the same offset. There is no slot-index arithmetic in these blocks. Moving the ID to a guessed slot-4 header location has no support here.
- Controller dispatch `0xa8ea20..0xa8eb20` has separate HMI and IC identities. Mode 1 reads model `+0xc`, publishes `[manID, HMI ID, -1]`; mode 0 reads `+0x10`, publishes `[manID, -1, IC ID]`. An invalid `0xffffffff` ID suppresses the notification in each branch. Four execution cases verify these outcomes.
- The notification boundary at `0xa86d30` is observed and skipped in the execution check. The downstream receiver is **not** executed. Static tracing shows this notification copies all three values, rather than collapsing the two RIC IDs into one.
- The next observer dispatcher `0xa86cf0..0xa86d2c` copies the complete three-word notification into each registered observer payload and invokes `0x2d9b00`. It does not select or validate an image there; identifying the concrete registered observer remains necessary.
- Previously traced PiP job setter `0xaa14dc` stores the selected RIC identity at job `+0x150`; when guidance-session `+0x28` is present it calls content setup and attachment. See [session binding](PIP-SESSION-BINDING-2026-11-18.md).

These findings narrow the investigation: the native metadata ID is a maneuver identity, not demonstrated to be a bitmap-slot index. The factory has an explicit identity-selection/attachment layer. Our matching local model/header values do not establish that this layer accepted the same image for the windshield. The branch names are grounded in the factory log's `RicManeuverID4HMI` and `RicManeuverID4IC`; they do not identify the active runtime branch in either failed test.

## Delivery boundaries

| Boundary | Evidence | What remains unproved |
| --- | --- | --- |
| Marker generated and posted | 255 frames per attempt; revision 2 active output scene contains the test window | Physical receiver consumed the output |
| Control messages accepted | Correlated setup acknowledgments; turn arrow observed | Acknowledgment validates pixel arrival or association |
| Header/model identity agrees locally | Producer contract verifies `0x0f000004`; fixed-offset producer evidence above | Receiver-selected RIC identity and physical pixel format |
| Resource description exists | Selected resource `0x02000004`; advertised limits respected | That resource is bound to the posted native image |
| Windshield receives an image | **No custom marker observed in either test** | This is the missing success condition |
| Cleanup and V1 return | Seven removal acknowledgments, resource absent, visual confirmation, V1 hashes/runtime verified | No new car check is required for this offline work |

The arrow establishes the maneuver/control path reached a display. It cannot distinguish a missing physical stream, a rejected image envelope, an unmatched receiver identity, or unsupported routing. No B009 events in the recordings do not establish the retained sink selection at test start.

## Next offline work, not a car request

Follow the notification consumer to the selected PiP job and identify which HMI/IC identity it forwards. Compare that identity chain to the submitted graph and the native stream envelope. Establish the downstream parser or routing contract before selecting another candidate. No factory receiver implementation is established in the retained HU binaries; HU-side instruction execution must not be labeled receiver verification.

Do not retry either failed candidate, move metadata fields by guessing, substitute G30 dimensions/packing beyond Supra limits, alter V1, or claim local Screen counters prove physical delivery. A new field test needs a specific evidenced change and a discriminating predicted result first.

## Reproduction and provenance

```sh
python tools/verify_pip_binding_records.py /private/NavigationFully /private/NavNBTEvoController
```

Dependencies: pyelftools and Unicorn. Binary identities:

- NavigationFully: `957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d`
- NavNBTEvoController: `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`

Private evidence bundle includes address-annotated traces and execution results. Factory code stays out of GitHub. Live evidence remains in [revision-2 result](PIP-REVISION2-RESULT-2026-11-18.md) and [first result](PIP-MARKER-RESULT-2026-11-18.md).

Credit: ryseek's native PiP work in Sq00ky/nanaisu's project provided the G30 implementation lead. See [source review and attribution](PIP-G30-REFERENCE-2026-11-18.md). That reference explicitly pauses its native video for HUD selection and does not establish Supra windshield delivery.
