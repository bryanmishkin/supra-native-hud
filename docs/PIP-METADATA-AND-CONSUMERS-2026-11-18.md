# PiP metadata image, HMI consumer, and external source review

18 November 2026. Offline continuation of [LayerManager pixel transport](PIP-LOCAL-PIXEL-TRANSPORT-2026-11-18.md). **V1 and the V2 runtime are unchanged. No vehicle access occurred. A larger windshield test is not yet ready.**

## New finding: PiP carries metadata in a tiny image

NavigationFully contains a distinct `PIPMetadata::paintSelf` implementation at `0x87bf00`. This is separate from the previously traced Ethernet PiP resource-description serializer.

- Constructor `0x87bb58` requests a **21×1** image through `0x8647f0`, with the four-byte color format selected. The creation diagnostic identifies that selection as `VG_sABGR_8888`.
- Metadata record size is **84 bytes**, copied by setter `0x87ba54` into item offset `0x14`.
- Junction-view update `0x7ee598` reads the current maneuver object's `+0x200` field into record offset `0x10`; another update does the same at `0x7f6464`. The `RICManeuverID` option parser stores its number at maneuver offset `0x200` (`0x86c5c4`). Current-maneuver lookup `0x7de388` names that object in its missing-maneuver diagnostic.
- Paint `0x87bf58` places the current context's 16-bit value at record offset 2. Do not conflate this field with the 32-bit RIC maneuver ID at offset 16.
- At `0x87c03c..0x87c064`, every four-byte group changes from `[a,b,c,d]` to `[b,c,d,a]`. The 84-byte result goes through `imageSubData` (`0x860f1c`) as a 21×1 update, then `drawImage` (`0x860a78`). This is an actual image update/draw path, not just a diagnostic string.
- This paint branch only proceeds when `0x88a8a8` returns null, while the previously traced command-mode PiP item requires a non-null result. The binary contains distinct native-image and command-description branches.

**Interpretation:** the native PiP picture has an in-image metadata convention, including a maneuver identifier. That is a concrete new lead for associating a video image with a PiP resource. It does **not** establish an active transport or receiver on this car. The final framebuffer channel order, metadata placement after composition, and cluster consumption remain unverified. Do not send this 84-byte block as a B006 upload payload.

### Executed validation, not just a rewritten algorithm

`tools/pip_metadata_strip.py` encodes/decodes the exact CPU-side upload block. `tools/verify_pip_metadata_codec.py` executes the captured ARM byte-rotation instructions in Unicorn and compares the result with the codec. The memcpy dependency is handled explicitly at its ABI boundary; the actual loop executes from the retained binary.

**259 vectors matched**, including zero, all-ones, sequential and deterministic random records; every inverse conversion recovered the original. The verifier checks the full NavigationFully SHA before using fixed addresses and limits execution to the small instruction block. This validates byte packing only, not a larger display or receiver behavior.

```sh
python tools/verify_pip_metadata_codec.py /private/path/NavigationFully
python tools/pip_metadata_strip.py /private/path/exact-84-byte-upload.bin
```

Dependencies for the instruction verifier: pyelftools and Unicorn. The codec uses the standard library only. Neither tool has network operations, vehicle commands or installation behavior.

NavigationFully SHA: `957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d`.
Executed instruction interval: `[0x87c03c,0x87c068)`; SHA `0271f9ea447e2cf5f64219c72cba23827f338e75a517f7dd38a710435f4f04a4`.

## HMI texture consumer is now identified

The LayerManager redirected texture is consumed by **CGfxWidgetLayer**:

1. Widget call `0x1cb8f68` invokes WAL virtual slot `0x8c`.
2. Captured `CWal3dNBTevo` vtable maps that slot to `0x2a057d4`; it calls `CHmiSurfaceRedirection`'s implementation at `0x2a0dd5c`.
3. The returned texture handle is assigned to the widget's member at offset `0xaf0` via `0x1cb8f78`.
4. Widget setup at `0x1cbda78..0x1cbdab4` binds that member to **`eParam_TextureHandle`**.

This identifies a local widget consumer. It does not join that texture to the Ethernet PiP resource, nor prove that no other exporter exists. The earlier assumption that “HMI texture → cluster PiP” is the next confirmed edge must remain a hypothesis.

The retained native-display snapshot shows screen output OTHER2 at 800×480 with an empty scene and no windows. LayerManager surface 1056 remains an unbound, zero-sized placeholder in that snapshot. Rechecking the retained BMPs confirms the first navigation buffer is byte-identical to the normal buffer; the second is a different buffer, not an established temporal update. Their pixel data alone cannot prove metadata placement or active PiP output.

## PiP disposal notification now reaches the request path

After the reference-counted resource removal described in the earlier report, observer `0xa8c150` selects the HMI or IC resource ID, skips `0xffffffff`, and calls `0xab2174`. That wrapper supplies the stored instance handle to `0xab2104`, which issues `MyRicDisposeResourceCall`.

The corresponding IPC handler `0x37b89c` passes handle and resource ID to `0xb9bed8`. The SOME/IP client wrapper at `0x2b11c0` calls `0xba31dc`; that request constructs **method 8** and serializes two big-endian 32-bit values through `0xba305c` / `0xba2ff0`. The response handler `0xba2ea8` dispatches a callback; `0x2b2648` implements the named `responseRic_disposeResource` callback.

This establishes the factory resource-disposal request format and callback machinery. It does not prove a live PiP acknowledgement, cancellation of every queued frame, or disappearance on the windshield. Local texture cleanup, source-stream stopping and receiver resource disposal remain separate checks. No factory IDs were touched.

## Other repositories: what their source actually provides

All review was read-only. No external installer, hook, activation utility or firmware was executed; no external implementation was copied into this app.

| Pinned source | Finding relevant to this task | Limit |
| --- | --- | --- |
| [st1ng/nbtevo-carplay-advanced, 9a80636](https://github.com/st1ng/nbtevo-carplay-advanced/blob/9a80636b5d8c6eee259105a5e9311b912935a9c7/src/kombi.h) | The source behind the linked CarPlay installer. `kombi.h` sends Ethernet route data; `hud.h` draws shapes through MOST HUDTerminal. Its README explicitly distinguishes these paths. | No arbitrary larger J29 PiP pixel upload found in the reviewed implementation. MOST shape drawing cannot be transplanted as proof for this Supra. |
| [ghackt/Carplay-advanced-installer, 8df8ab7](https://github.com/ghackt/Carplay-advanced-installer/blob/8df8ab72fced3101066f4ac83cbf32d1e070a209/README.md) | Identifies st1ng's project as its payload source. Reviewed tree contains installer/payload releases and documentation. | Installer screenshots are not evidence of a new J29 pixel channel. Source review followed the payload upstream. |
| [ftojke/BMW-iDrive6-CarPlay-HUD, 97b9133](https://github.com/ftojke/BMW-iDrive6-CarPlay-HUD/blob/97b91338789a93c3638f1895ddc2ed5ee5f194f9/hook/cp_kombi.cpp) | Maps CarPlay maneuvers into the Ethernet KOMBI guidance graph; reviewed graph source derives from NBT-AAD. | Structured navigation rendering, not the missing native texture transport. |
| [Sq00ky/Supra-iDrive6-Android-Auto, 225728a](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/225728ad78cfdf6a558896bc6f6a04128f01a490/milestone-7/src/cluster/j29_graph.hpp) | J29 graph and resource/model construction remain the closest transport reference. Existing local checkout `87fd962` additionally documents native center-display surfaces. | No arbitrary PiP pixel source in the reviewed J29 files. Connector's pinned HEAD differed from the existing local checkout; both revisions are recorded rather than called one current version. |
| [inotbarnacle/ID6_apps_prerelease, 5d19aa1](https://github.com/inotbarnacle/ID6_apps_prerelease/blob/5d19aa12b961144a28afc8d96c1327941c4212c3/AgentReadMe.md) | HUD Gauges requires the reference MOST HUDTerminal 82/00 at node 0101. | Different renderer/interface; no J29 PiP solution established by its instructions. |
| [agent00jackson/bimmulator, bf03f2e](https://github.com/agent00jackson/bimmulator/blob/bf03f2eed11969c1450a64fe5ba301a5ed128257/NATIVE_GRAPHICS_CONTRACT.md) | Independent graphics investigation describes RemoteEGL shared images. Its cluster firmware helper targets Bosch BO03 6WB. | Emulator/local graphics and a different cluster; not evidence of our receiver or installed firmware. No firmware was downloaded. |
| [herrbimmer/IDEmu, d03ecd8](https://github.com/herrbimmer/IDEmu/blob/d03ecd84f3635e54cf09a271230a54fc88373251/src/shim/ilm.c) | Exact-symbol search found a redirection shim; it tracks map surface 0x201 and redirection state. | Emulated behavior, not real cluster PiP transport. |

Exact GitHub searches for `RICManeuverID` and `PictureInPictureElementStruct` returned no matches; `PIPMetadata` returned unrelated code. These bounded search results do not establish that no public solution exists.

## What remains before a larger drawing test

We now have the native metadata-image format, a named HMI texture consumer, and the disposal request path. We still lack an established **active output-to-cluster pixel connection and receiver-side image binding** for this Supra. No source reviewed supplies that missing edge.

The next offline target is the native image/output path carrying the 21-pixel metadata strip, including where its maneuver ID becomes the cluster's PiP image identity. Keep it separate from the HMI widget texture until an actual call or configuration joins them. A live test must name that transport, allocate only owned resources, stop the producer, dispose the receiver image and verify removal before V1 resumes. The tools added here deliberately do not guess a display number or expose a live drawing mode.

### Located, but not present in the saved file set

The saved `library-inventory.txt` identifies the active `graphics.conf` symlink target as `/lib/graphics/omap5430/graphics-1280_480.conf` (3,863 bytes), plus `libWFDomap5430ES2_0.so` (223,172 bytes), `libwfdcfg-emodule-hu.so` and `libwfdcfg.so.0`. These are output-driver/configuration components; they were not part of the previous LayerManager ELF dependency closure. The current filesystem search of Documents/Downloads did not find standalone copies. Unexpanded archives were not exhaustively searched.

The read-only `collect_pip_router.py` plan now includes these exact inventory-backed files, both the symlink and target configuration contents, and the current `screen` process map in addition to LayerManager's map. It still defaults to an offline plan, double-reads files, changes no display state and marks drawing readiness false. This is a prepared evidence capture for a future connection if needed, **not a request to return to the car now and not a larger-display test**. The earlier 30-file capture remains complete for its stated scope; it did not establish the output-driver route.
