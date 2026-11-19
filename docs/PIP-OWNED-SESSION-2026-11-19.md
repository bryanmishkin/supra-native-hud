# Owned guidance session and picture capability

Offline trace against the captured controller, NavigationFully and MOCCA library. No vehicle contact; V1 files and runtime unchanged. This identifies concrete protocol and rendering dependencies, not a demonstrated larger windshield drawing test.

## Creation and identity

Controller RegisterGuidanceSessionCall reaches DNAVIManeuverView method 3. Its payload is two 32-bit fields: maneuver ID and guidance type. The controller applies style-client bits `0x03000000`; decimal types 8301/8402 are hexadecimal `0x206d`/`0x20d2`, not `0x8301`/`0x8402`.

Native union dispatch `0x1d3250` selects writer `0x1d6df8`. The stream boundary receives eight little-endian bytes, demonstrated by `tools/verify_guidance_request_payload.py`. The captured MOCCA library's buffered `doWrite` branch preserves those bytes (`tools/verify_mocca_stream_buffer.py`). Native MOCCA flush and Colibry TCP send also produce identical complete unfragmented frames (40-byte routing header, 16-byte request prefix, payload) for equal synthetic routing inputs and sequence 37. `tools/verify_dsi_frame_equivalence.py` checks method 3 twice and zero-payload method 7 against both captured libraries. Socket calls are intercepted; this does not prove a valid live service binding or response semantics.

The returned pair is guidance session and MOCCA session. Controller completion `0xabd5f0` stores them separately at owner+0x70/+0x74. The guidance session propagates to command data+0x1b4 and then the display attachment. The drawing resource handle is neither identifier.

NavigationFully admission `0x6149f8` accepts maneuver ID 0 or -2 without borrowing an existing factory maneuver. Other IDs require a current registry entry. Accepted requests create a CGVView and CGVViewSet. Admission does not ensure its selected style produces an image or reaches the windshield.

## Picture permission and actual model field

Captured configuration tag 19 decodes to high-intersection picture support **enabled**, metadata-content support disabled. Native decoder `0xbc8c78`, config dispatcher `0xa24ca4`, and high-intersection serialization gate are exercised by `tools/verify_pip_picture_permission.py`.

For model type 7, `0xa8b984` links the converted PiP resource into the model's destination-specific picture field (+0x34 HMI / +0x38 IC). `sendIntersectionHighElement` at `0xab4750` includes that ID when the picture permission is enabled; disabled permission substitutes UINT_MAX. Thus lack of this advertised permission does not explain our failed custom image. No receiver pixel association is inferred from the permission flag.

## Style definitions are external input

The selected `nav_styles.ini` names directory `/opt/nav/eceusa/bin/gvStyleDB_ID5_NBTEvo_BMW_USA_1025`. Its existence is in the retained directory listing, but its contents are absent from retained filenames and 163 scanned ZIP archives.

Native guiding accessor selects style index/category 4/variant 0 in the content index. The returned mapped blob is interpreted as XAR, whose first XPD supplies typed properties. `guiding.*.viewStyle`, indexed by requested type, supplies four header words and five-word element records. `0x7de844` dispatches each element's renderer type. A missing or unsuitable property fails view creation; selecting a known numeric type alone is insufficient.

`tools/capture_guidance_styles.py` prepares an offline-default read-only collection of that exact directory and `style_config`, plus the selected INI. It uses regular-file enumeration, bounded transfers, double reads, local hashes, and V1 baseline/fault checks. It performs no drawing, restart, hook or remote write. It has not been run on the vehicle.

## Cleanup must finish asynchronously

Unregister is DNAVIManeuverView method 7, zero payload, correlated using the retained MOCCA sequence. Navigation's handler creates opcode-7 disposal command, resolves the guidance view, invalidates attached tokens, and removes the active view. A child-state predicate can defer destruction until later manager idle cycles. Receipt of unregister alone is not proof of completed image removal.

`tools/verify_guidance_cleanup.py` executes the native command constructor and attachment invalidation, including already-cleared idempotence. Notification allocation/delivery/destruction are explicitly intercepted; their delivery and physical image absence remain untested.

## Remaining implementation work

Resolve actual style element definitions and linked resources; finish owned MOCCA service bootstrap and response correlation; attach the returned guidance session through its valid displayable context; prove the receiver's pixel association; verify asynchronous cleanup before any live runner is admitted. No guessed factory IDs, captured pointers, forced readiness flags, or replacement of the working V1 installation are justified by this trace.
