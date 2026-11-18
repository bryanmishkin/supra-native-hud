# PiP session binding trace — 18 November 2026

This continues the [per-flow pixel-path analysis](PIP-PIXEL-PATH-2026-11-18.md). All work is offline against the retained reference binaries. V1 code, installed files, tags and startup behavior are unchanged. **This is not an executable larger-display test.**

## Resolved attachment target

The previously unresolved call at controller `0xa7c690` is now resolved through construction and the vtable:

1. `CRicDisplyableSessionForPiPDisICHUD` constructor `0xa7b0c8` allocates an object, calls `0xa83ab8`, and stores it at session offset `0x20`.
2. `0xa83ab8` identifies that object as `CRicPiPDisICHUDDataTask`. It installs vtable `0x1058f00` at object offset zero.
3. Vtable slot `0x14` contains `0xa82cbc`, so `handleAttachView PiPDisplayable` dispatches to that concrete `scheduleAttachView` implementation.
4. `0xa82cbc` records the requested maneuver ID at task offset `0xa4`, searches its job vector at `0x30..0x34` for a job whose offset `8` matches, then calls the job's vtable slot `0x10` with the guidance-session argument. No match means no attachment in this function.
5. Task job factory `0xa83170` constructs `CRicPiPDisplayableICHUDJob` via `0xaa0f94`. Its vtable is `0x105d748`; slot `0x10` points to `0xaa155c`.

Thus this is an existing-maneuver/job attachment path, not a raw pixel upload or a call that creates an independently owned windshield canvas.

## The native view is bound by RIC maneuver identity

`0xaa155c` stores the guidance-session ID at job offset `0x28`. If the RIC maneuver ID at `0x150` is still `0xffffffff`, it logs `RicManeuverID not set` and does not issue the two attachment operations. Otherwise:

- `0xaa136c` formats **`RICManeuverID=%d`**, places it in a content item (type value 5), and constructs the `sendSetContent` call for the guidance session.
- `0xaa11d4` constructs `AttachGuidanceSession` using the guidance-session ID, displayable-session value, maneuver ID and guidance type.
- Setter `0xaa14dc` stores a later RIC maneuver ID and performs these same calls when a guidance session is already present. The two identities may therefore arrive in either order; recording only window creation misses an essential binding edge.

The registration result handler `0xa7c7c4` accepts only its outstanding request, stores the returned session value, and copies it into the data task. A rejected or unrelated registration result is not equivalent to a usable displayable session.

On the producer side, NavigationFully `0x86c584..0x86c5c4` recognizes the exact key **`RICManeuverID`**, converts its string value and stores it at the receiving object's offset `0x200`. This confirms a matching content setting exists on both sides. The complete propagation from that field into the rendered window/receiver transport remains untraced; do not equate it with a PiP resource ID or framebuffer address.

## PiP command output still contains metadata, not pixel bytes

NavigationFully `CGVHgPiPInfoItem::paintSelf` at `0x87c780` requires its enabled flag and a command-output object. Its calls at `0x87c7f8..0x87c85c` write a chunk identifier, maneuver type, resource type, two dimensions, color depth, packaging, and a picture ID from render context offset `0x54`, then finalize the chunk. The corresponding diagnostic explicitly labels the last value `picture ID`.

There is no image byte array in this function. It supplies the metadata consumed by the controller's previously traced HGPictureInPicture parser. This does **not** prove that no separate image transport exists; it narrows where not to append pixels. The connection between render-context `0x54`, the RIC maneuver setting and the actual native-window export remains a distinct trace target.

## Sink and cancellation limits

The `MySinkSwitchNotification` handler calls both PiP command/display session interfaces and reports an error if either is absent (`0xa7a448..0xa7a50c`). That is consistent with paired session plumbing, not an independently selectable free rectangle. The earlier live window remained invisible while model-based windshield guidance worked.

The PiP display job's `processCancel` at `0xaa0bd4` calls `0xa9435c`. That routine writes the maneuver ID to a callback object, invokes `0x2dbf24`, and clears its callback pointer. The destructor also tears down the base job and callback storage. **Neither inspected routine proves receiver image deletion, detach completion or release of an app-owned window.** A successful local cancellation cannot substitute for visible cleanup verification.

## Exact larger-test readiness gap

A defensible larger V2 test needs all of these edges, not merely a 320×320 descriptor accepted by B006:

| Edge | Evidence now | Still required |
|---|---|---|
| Native pixel producer | Type-0 EGL window surface; actual window 1056 retained | How a new app supplies pixels without borrowing the factory window |
| Identity binding | RIC maneuver content key and guidance-session attach resolved | Mapping to receiver PiP resource and physical windshield output |
| Transport | PiP command and B006 descriptor are metadata-only | Actual image export/stream endpoint, format and ownership |
| Removal | Factory job cancellation callback located | Detach/release completion and disappearance of only our content |

No live PiP activation, buffer overwrite or speculative larger bitmap upload has been prepared. That would skip the unresolved transport and cleanup edges. The next offline investigation is the propagation of NavigationFully's RIC maneuver setting and render-context picture ID into the native-window output, plus the final sink consumer. If those edges reside in an uncaptured compositor or receiver component, identify the exact component before asking for another car visit. The current evidence is insufficient to promise an executable larger-display test.

## Provenance

Controller SHA-256: `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`.

NavigationFully SHA-256: `957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d`.

Private archive includes bounded disassembly extracts, string-reference scans, vtable words, reproduction scripts and a file-hash manifest. Literal pools are data, not executable instructions. No OEM bytes, private route data or credentials are added to GitHub.

Follow-up: [transport boundary and reference-counted removal](PIP-TRANSPORT-BOUNDARY-2026-11-18.md) identifies the missing layer-manager capture and a targeted read-only collector.
