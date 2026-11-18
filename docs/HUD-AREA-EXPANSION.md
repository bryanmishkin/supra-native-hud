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
