# HUD area expansion investigation — 18 November 2026

Offline research only. No vehicle connection, installed-file change, or larger-area drawing test was performed. V1 baseline and V2 runtime behavior remain unchanged.

## What we can establish

The current renderer and upload encoder use **150 × 36 pixels**. This is also the bitmap resolution returned in the retained successful B006 create reply, not merely a layout choice. The traced bitmap configuration reports ten resources starting at 0x01000000, with RLE32 enabled. The app uses only slots 8/9.

The image is bound through the shared factory coming-road model. Removing the navigation symbol suppresses that symbol; it does not establish ownership of its former screen area. Increasing the source pixel count could be rejected, scaled, or clipped. Improving edge quality inside the current bitmap is distinct from increasing its physical windshield footprint.

Evidence: `src/tach_bitmap.cpp`, `src/standalone_wire.cpp`, `RIC-BITMAP-RESOURCE.md`, `RIC-GUIDING-BINDING.md`, and the retained `profile-probe/001-response.bin`. Reply SHA-256: `2740bccc5fc25fd6bc983ecd69fc98792ad1c073e220a4a3c1c23f3bc12f676e`.

## Concrete unresolved lead

The same reply includes configuration variant **35**, 16 bytes long. Two big-endian 16-bit values at offset 10 are **320, 320**. Their semantics, resource type, and visible-image binding have not been traced. This is a candidate geometry lead, **not proof of a 320 × 320 windshield surface**. Variant 30 also ends in a 150,36 pair; that tail is not established as a writable placement control.

The offline auditor `tools/audit_hud_geometry.py` reproduces these observations and explicitly reports `larger_windshield_surface_proven: false` and `live_test_ready: false`. It accepts a retained reply and writes JSON; it has no network or drawing operations.

## Other repositories reviewed

| Source | Useful evidence | Limit |
| --- | --- | --- |
| [Sq00ky/Supra-iDrive6-Android-Auto](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto) | J29-specific Ethernet guidance graph, factory model bindings and lanes. Closest transport/model match. | Reviewed J29 files do not establish a larger arbitrary bitmap canvas or free XY placement. Separate MOST HUD code must not be treated as J29 proof. |
| [FarazzShaikh/j29-supra-id6-assets](https://github.com/FarazzShaikh/j29-supra-id6-assets) | Supra-specific extracted HMI assets, including Headup_preview artwork. | These are HUD settings preview assets on the center screen; their dimensions do not establish windshield geometry. |
| [Sq00ky/Supra-Headunit-RE](https://github.com/Sq00ky/Supra-Headunit-RE) | Supra head-unit reverse-engineering background. | No larger windshield surface established by the bounded review. No access-modification instructions were executed. |
| [inotbarnacle/ID6_apps_prerelease](https://github.com/inotbarnacle/ID6_apps_prerelease) | Visually relevant HUD Gauges design and deployment reference. | Its AgentReadMe requires MOST HUDTerminal service 82/00, node 0101. This is not direct proof for our J29 Ethernet B006 drawing path. |

The closest source was reviewed at commit `225728ad78cfdf6a558896bc6f6a04128f01a490`: [J29 graph](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/225728ad78cfdf6a558896bc6f6a04128f01a490/milestone-7/src/cluster/j29_graph.hpp), [graph template](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/225728ad78cfdf6a558896bc6f6a04128f01a490/milestone-7/src/cluster/j29_graph_template.hpp), and [display](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/225728ad78cfdf6a558896bc6f6a04128f01a490/milestone-7/src/cluster/j29_display.cpp). These are references, not copied implementation code.

## Next trace and admission criteria

1. Identify variant 35's serializer/deserializer and resource type in the retained controller. Follow the associated image binding to determine whether it reaches the windshield, cluster, or both.
2. Trace the model configuration geometry and clipping/scaling behavior. Do not assume returned configuration values can be changed by a client.
3. Only after a supported resource and binding are established, prepare one bounded static-marker candidate with exact dimensions, owned-resource checks, removal verification and rollback. Compare windshield and cluster separately.
4. Keep telemetry and startup unchanged during any future geometry experiment. A larger image upload acknowledged by the receiver is insufficient; visible size and clipping require observation.

No additional car visit is requested by this investigation. Expansion remains unproven; the 320-pair resource trace is the strongest concrete offline next step.

## Follow-up: variant 35 identified as picture-in-picture

Further offline tracing on 18 November identifies the configuration family:

- `setAllConfigInfo` reads the configuration discriminator at `0xa2633c`, subtracts one, bounds it to 39 entries, then dispatches through the table at `0xa26350`.
- Entry 35 at `0xa263d8` points to `0xa2643c`. That branch explicitly checks union tag `0x23` (35) at `0xa2644c` and calls `0xa26008` at `0xa2645c`.
- The called setter logs **setPictureinPictureConfig**. It iterates a 16-bit resolution vector from the incoming structure at offset `0x10`, logs **mMaxResolution**, and stores resource count/offset and color depth/packaging fields.
- The adjacent road-list setter logs **maxRoadIconSize**, as well as maximum road entries, icon count and text count. This strengthens the interpretation that current road-icon geometry is a model limit, rather than an arbitrary renderer constant.

Thus variant 35 is now identified as the **picture-in-picture configuration family**. The saved reply's 320,320 pair is a strong candidate for its maximum resolution. The wire-to-object deserializer still needs to be followed before treating that specific pair as a formally decoded field. It is not a larger bitmap allowance for resource type 1.

The earlier `RIC-BITMAP-RESOURCE.md` trace already identifies a local picture-in-picture resource staging choice in the detailed-navigation builder (`0xaa7b44`, called from `0xaa7c20`). That is a concrete next binding path, but does not establish an independently writable picture-in-picture surface or its windshield placement. Local builder selectors, resource-wire enums and configuration tags are distinct domains.

Next: follow the variant-35 wire decoder and picture-in-picture upload/staging path, then its visible detailed-maneuver binding. Determine whether the resource carries pixels, a stream reference or another representation, and whether it reaches the windshield. Do not enlarge the existing RLE32 bitmap or send a speculative picture-in-picture request based on the configuration name alone.

Trace provenance: same controller SHA-256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`; retained extracts in the private `hud-expansion-trace-2026-11-18` archive. Literal pools were read as words, not treated as executable instructions. This remains static evidence, not vehicle acceptance.
