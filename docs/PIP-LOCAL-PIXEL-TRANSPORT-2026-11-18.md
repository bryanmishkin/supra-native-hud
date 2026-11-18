# LayerManager pixels reach an HMI texture — 18 November 2026

Offline analysis of the verified LayerManager capture closes a real pixel-copy and consumer path. **It does not yet establish a larger windshield drawing test.** V1, startup files, runtime source and the installed vehicle were not changed. The car was disconnected throughout this analysis.

## Proven chain

Native Screen window → LayerManager RemoteEGLImageSource → shared image/metadata → signal to requesting process → HmiMain3D surface-redirection receiver → EGL image / OpenGL external texture.

The word “remote” here does not itself establish a network or cluster destination. We found an actual HmiMain3D consumer, not just a matching name. This is a useful local rendering mechanism; a subsequent windshield exporter remains unproven. Do not describe it as center-screen-only either: the final downstream routing has not been established.

| Component | Verified call sites / behavior |
| --- | --- |
| LayerManagerService | `0x124e50` setup builds `dev/layermanager_<surface>_img` and `_cmd` names, passes target PID, surface ID, Screen context and native window into RemoteEGLImageSource initialization at `0x124f2c`. |
| libcommunication_graphics | Source init `0x4088` obtains dimensions, computes width × 4 stride, opens shared image storage and 0x48-byte metadata storage. Source update `0x3334` copies the window with `screen_read_window` at `0x33b8`; success queues signal 17 with surface ID to the configured PID at `0x34a0` onward. This is local shared memory plus process notification. |
| HmiMain3D | Installs signal 17 handler at `0x2a0df50`; invokes `ilm_startSurfaceRedirect` at `0x2a0dffc`. Opens shared memory at `0x2a0d904`, maps metadata at `0x2a0d968`, and uses `mmap_device_memory` at `0x2a0dbe8`. |
| HmiMain3D image binding | Resolves `glEGLImageTargetTexture2DOES` and `eglCreateImageKHR` from strings loaded at `0x2a0e588` / `0x2a0e598`. Calls the image constructor through r4 at `0x2a0e698`, creates/binds a texture at `0x2a0e6ac` / `0x2a0e6b8`, and invokes the image-to-texture function through r8 at `0x2a0e704`. Texture target immediate is `0x8d65`. |
| HmiMain3D updates | Exported `CHmiSurfaceRedirection::notifyUpdate` at `0x2a0c51c` forwards the signal payload to `0x2a0c498`, which finds the surface entry and marks it dirty. |

These addresses refer to the captured ARM binaries, not host process addresses. Static code establishes implementation; it does not prove that surface 1056 exercised this chain during the capture.

## Removal is now traced on both sides of this local path

HMI cleanup `0x2a0cf90` calls `ilm_stopSurfaceRedirect` at `0x2a0cfc0`, invokes mapping cleanup `0x2a0cd04`, and deletes the texture at `0x2a0d04c`. Mapping cleanup contains `munmap` and `shm_unlink` calls.

LayerManager teardown `0x123428` invokes source destroy and clears its forwarding flag. Graphics source destroy `0x36b8` tears down its image, metadata and shared-memory objects. Image teardown `0x34d4` removes Screen notification and destroys the source pixmap/buffer handles.

This is **redirection-copy cleanup**, not permission to destroy the original factory window. It also does not prove disposal/acknowledgement for the cluster's PiP resources. Those are separate ownership domains. Existing V1 slots 8/9 and its cleanup remain unchanged.

## Why this is not an executable larger-HUD test yet

The live capture found LayerManager surface 1056 as a zero-sized placeholder, native-surface value `0xffffffff`, no layer and zero update counters. Its existence is not an active native window binding. The previously captured PiP configuration advertises a 320×320 resource, but the PiP resource serializer carries metadata, not an arbitrary pixel array.

Still needed offline:

1. Trace the consumer of the HMI texture / RIC maneuver binding to a concrete cluster or windshield export, or rule out this local redirection path for that purpose.
2. Establish how an owned image is associated with a specific PiP resource and output display. Do not substitute surface ID 1056 or a screen number as an unproven routing selector.
3. Follow PiP disposal notifications through the receiving interface and establish acknowledgement and owned-resource checks. Local GL/shared-memory destruction alone is insufficient.

No new car session is requested from this result. No script in this change connects to the car or issues drawing commands. A larger test remains explicitly **not ready** rather than shipping an unbound native-window demo.

## Reproduction and evidence

New `tools/trace_arm_import_calls.py` inventories ARM import calls and resolves literal linker veneers (`ldr pc,[pc,#-4]`). This matters because the HMI's surface-redirection calls branch through veneers; direct PLT-call search falsely appeared empty. The script reads an ELF only and rejects unsupported architecture, PLT layout, unaligned or oversized regions. Linear results still require control-flow review.

```sh
python tools/trace_arm_import_calls.py /private/path/HmiMain3D \
  --start 0x2a0c558 --size 0x2ea8 > /private/path/hmi-import-audit.json
```

Requires capstone and pyelftools. Validation on the retained HMI matched seven selected calls: start/stop redirect, signal registration, shared-memory open/map, and texture creation/deletion. Private archive retains bounded disassemblies, resolved imports, extension-name resolution, scripts, hashes and this report; OEM binaries remain outside Git.

Binary identities:

- LayerManagerService: `8a85b61891f0f96f4927b1eccefaa5d31821c7eb9eaf317484f723ac880256b1`
- HmiMain3D: `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`
- Supporting library identities are recorded in the private capture's verified-file manifest and each bounded trace JSON.

See [capture provenance](PIP-LAYER-CAPTURE-2026-11-18.md), [prior transport boundary](PIP-TRANSPORT-BOUNDARY-2026-11-18.md), and [session binding](PIP-SESSION-BINDING-2026-11-18.md). Historical reports remain evidence; this document advances their unfinished LayerManager trace.
