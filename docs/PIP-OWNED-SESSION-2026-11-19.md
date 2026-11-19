# Owned guidance session and picture capability

**Capture update:** the selected styles are now saved and 210 actual view lookups match native ARM execution. See [selected-style results](SELECTED-STYLE-RENDERING-2026-11-19.md). Earlier missing-file statements below describe the pre-capture state. No larger windshield binding is claimed.

Offline trace against the captured controller, NavigationFully and MOCCA library. No vehicle contact; V1 files and runtime unchanged. This identifies concrete protocol and rendering dependencies, not a demonstrated larger windshield drawing test.

## Creation and identity

Controller RegisterGuidanceSessionCall reaches DNAVIManeuverView method 3. Its payload is two 32-bit fields: maneuver ID and guidance type. The controller applies style-client bits `0x03000000`; decimal types 8301/8402 are hexadecimal `0x206d`/`0x20d2`, not `0x8301`/`0x8402`.

Native union dispatch `0x1d3250` selects writer `0x1d6df8`. The stream boundary receives eight little-endian bytes, demonstrated by `tools/verify_guidance_request_payload.py`. The captured MOCCA library's buffered `doWrite` branch preserves those bytes (`tools/verify_mocca_stream_buffer.py`). Native MOCCA flush and Colibry TCP send also produce identical complete unfragmented frames (40-byte routing header, 16-byte request prefix, payload) for equal synthetic routing inputs and sequence 37. `tools/verify_dsi_frame_equivalence.py` checks method 3 twice and zero-payload method 7 against both captured libraries. Socket calls are intercepted; this does not prove a valid live service binding or response semantics.

The local completion pair is guidance session and retained MOCCA request sequence. It is **not** a verbatim pair from the wire. Response event `0x80000000` decodes two u32 fields, but handler `0x3109ac` copies only its first field into the call object; its second local word already holds the outbound sequence from `0x310f34`. `tools/verify_guidance_response_payload.py` executes this distinction with three cases. The second wire field is result/status: provider `0x1f4f3c` and emitter `0x5872bc` prove the pair is session ID plus result. Missing maneuver gives result 2; result 0 alone does not prove style content or pixels. `tools/verify_guidance_response_emitter.py` distinguishes the internal unblock token from both serialized fields. Controller completion `0xabd5f0` stores the local pair separately at owner+0x70/+0x74. The guidance session propagates to command data+0x1b4 and then the display attachment. The drawing resource handle is neither identifier.

NavigationFully admission `0x6149f8` accepts maneuver ID 0 or -2 without borrowing an existing factory maneuver. Other IDs require a current registry entry. Accepted requests create a CGVView and CGVViewSet. Admission does not ensure its selected style produces an image or reaches the windshield.

## Actual service and owned update subscription

The generated provider exports `ManeuverView.DNAVIManeuverView`, version **32.0**. `tools/verify_maneuver_export.py` executes its exact captured constructor without intercepted calls. The component-information label and version are not interchangeable with the broker export.

Displayable creation requires two framework requests on the **same owned client route and sequence**: first request type `0x105`, event `0x80000004`, empty payload; then request type `0x100`, method 4, its registration payload. Native proxy `0xc27428` registers Data through `CHBRegisterProxyBase::setRegistryNotification`; MOCCA `0xb1010`/`0xb1170` sends the registry notification under the upcoming create transaction. This is not an invented DNAVI method 5 or an unscoped generic notification.

`guidance_payload.py` and `tools/pip/include/guidance_payload.hpp` now build this paired handshake. They perform no I/O. `verify_dsi_owned_sequence.py` verifies that the native Colibry constructor retains a supplied nonzero sequence; zero instead asks the allocator for a new one. `verify_dsi_frame_equivalence.py` includes the `0x105` frame in its MOCCA/Colibry comparison. A live client still must allocate/retain its sequence and prove its broker route. Targeted listener removal uses request type `0x106`, the same Data event and the original registration sequence; the paired release builder then emits method 6. The convenience Colibry `setNotification`/`clearNotification` instead use `0x101`/`0x102` and sequence zero, so they cannot substitute for this contract. `verify_registry_subscription_controls.py` executes these differences natively.

Data event `0x80000004` contains `userId`, a length-prefixed unpadded shared-memory name, `maneuverId`, `guidanceType`, byte count and sequence. **Its first field is the caller’s user ID, not the allocated displayable session.** The controller explicitly filters user IDs and maneuver/type associations before consuming bytes. `verify_displayable_data.py` executes the native serializer and checks the bounded Python decoder. Metadata receipt is not proof of ownership, current frame bytes or windshield delivery.

## Picture permission and actual model field

Captured configuration tag 19 decodes to high-intersection picture support **enabled**, metadata-content support disabled. Native decoder `0xbc8c78`, config dispatcher `0xa24ca4`, and high-intersection serialization gate are exercised by `tools/verify_pip_picture_permission.py`.

For model type 7, `0xa8b984` links the converted PiP resource into the model's destination-specific picture field (+0x34 HMI / +0x38 IC). `sendIntersectionHighElement` at `0xab4750` includes that ID when the picture permission is enabled; disabled permission substitutes UINT_MAX. Thus lack of this advertised permission does not explain our failed custom image. No receiver pixel association is inferred from the permission flag.

## Style definitions are external input

The selected `nav_styles.ini` names directory `/opt/nav/eceusa/bin/gvStyleDB_ID5_NBTEvo_BMW_USA_1025`. Its existence is in the retained directory listing, but its contents are absent from retained filenames and 163 scanned ZIP archives.

Native guiding accessor selects style index/category 4/variant 0 in the content index. The returned mapped blob is interpreted as XAR, whose first XPD supplies typed properties. `guiding.*.viewStyle`, indexed by requested type, supplies four header words and five-word element records. `0x7de844` dispatches each element's renderer type. A missing or unsuitable property fails view creation; selecting a known numeric type alone is insufficient.

`tools/capture_guidance_styles.py` prepares an offline-default read-only collection of that exact directory and `style_config`, plus the selected INI. It uses regular-file enumeration, bounded transfers, double reads, local hashes, and V1 baseline/fault checks. It performs no drawing, restart, hook or remote write. It has not been run on the vehicle.

## Cleanup must finish asynchronously

Displayable registration returns one u32 session ID in event `0x80000003`. Displayable removal is method 6, empty payload, correlated by the original registration sequence; the provider maps client identity plus that sequence back to its registered displayable. Attach response event `0x80000001` carries a boolean result. Neither request disposal nor its queueing proves physical removal.

Guidance unregister is DNAVIManeuverView method 7, zero payload, correlated using the retained MOCCA sequence. Navigation's handler creates opcode-7 disposal command, resolves the guidance view, invalidates attached tokens, and removes the active view. A child-state predicate can defer destruction until later manager idle cycles. Receipt of unregister alone is not proof of completed image removal.

`tools/verify_guidance_cleanup.py` executes the native command constructor and attachment invalidation, including already-cleared idempotence. Notification allocation/delivery/destruction are explicitly intercepted; their delivery and physical image absence remain untested.

## Remaining implementation work

Resolve actual style element definitions and linked resources; finish owned MOCCA service bootstrap and response correlation; attach the returned guidance session through its valid displayable context; prove the receiver's pixel association; verify asynchronous cleanup before any live runner is admitted. No guessed factory IDs, captured pointers, forced readiness flags, or replacement of the working V1 installation are justified by this trace.
