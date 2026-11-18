# Output-driver trace: physical video, not an established Ethernet PiP uploader

Offline analysis of the [completed driver capture](OUTPUT-DRIVER-CAPTURE-2026-11-18.md). V1/runtime/startup are unchanged. No car connection, hardware call, configuration change or live drawing was performed. **A larger windshield drawing test is still not ready.** The evidence now identifies what the second output actually implements instead of inferring its purpose from its dimensions.

## Executed port-selection contract

`tools/verify_output_driver_contract.py` executes the captured ARM `wfdcfg_port_create` routine in Unicorn. Only allocator/free calls are handled locally; unexpected external calls abort. Exact input hashes are checked before loading. IDs 1 and 2 succeed; tested IDs 0, 3 and 99 return 2.

| Port | Returned extension table |
| --- | --- |
| 1 | `invert_data_line=1` |
| 2 | `port_init1 → 0x2b34`, `port_uninit1 → 0x2a74`, `port_set_mode2 → 0x29b0`, `enable_rgba_over_rgb=1` |

The second port's initialization calls `port_get_driver_path` and then `tda19988_init`. Its mode callback calls `tda19988_set_mode`; teardown calls `tda19988_fini`. The path chooser checks the captured I2C device-path strings. NXP identifies TDA19988 as an HDMI transmitter ([manufacturer support](https://community.nxp.com/t5/NXP-Designs/TDA19988-Input-format/m-p/1063841)). This establishes a physical transmitter implementation. It does **not** establish where this reference car wires that output, or a cluster/windshield receiver for it.

## Width conversion is transport packing, not extra drawing area

The same verifier executes `port_set_mode2`, intercepting `tda19988_set_mode` solely to record its argument structure. The hardware-facing routine is **never executed**. Sixteen cases cover conversion on/off for eight widths. All preserve the other six words in the argument record.

With conversion enabled, the callback increases the width in steps of 32 until divisible by 3, then multiplies by 4/3:

| Input width | Transmitter width |
| --- | --- |
| 150 | 200 |
| 320 | 512 |
| 640 | 896 |
| 800 | 1152 |
| 1280 | 1792 |

With conversion disabled, width remains unchanged. This is consistent with the named RGBA-over-RGB extension. It is **not** proof of final pixel channel order, metadata positioning, physical receiver support, or more usable windshield pixels. Do not replace the app's bitmap width with the transmitter width.

## Screen-to-driver submission is now located

The captured screen executable imports and calls these WFD operations:

| Caller | Call site | Operation |
| --- | --- | --- |
| `win_composition_init` | `0x1241a4`, `0x124554` | Create source from image |
| `win_stream_realize` | `0x13e6c8` | Create source from image |
| `win_plane_init` | `0x124e90` | Bind pipeline to port |
| `win_draw` | `0x12fd24`, `0x12fd54`, `0x12fd84`, `0x12fe50`, `0x12fe84` | Bind image source to pipeline |
| `win_update` | `0x1305d0` | Device commit |
| `win_display_fini` | `0x1237a4`, `0x1238a0`, `0x1238b0` | Source-binding changes and device commit |
| `win_death_row` | `0x12eeb0` | Destroy source |

These call-site inventories require control-flow context; they are not an ownership-safe live recipe. In the OMAP driver, `wfdCreateSourceFromImage` is implemented at `0x246b4`; `wfdBindSourceToPipeline` at `0x1aedc`; `wfdDeviceCommit` at `0x6830`. Register mapping at `0x131ec` includes a `disp_mmap_device_memory` call at `0x1339c` with physical base `0x58000000`. This is local display-hardware submission, not an identified SOME/IP pixel sender.

The specifically named `wfdCreateSourceFromStream` entry at `0x24430` is only `mov r0,#0; bx lr`. Actual ARM execution with three different argument sets returns zero without external calls. This rules out **that entry point** as a working stream-source API in this driver. It does not rule out every stream mechanism: screen's own `win_stream_realize` uses image sources, and screen contains separate destination/writeback machinery. Do not generalize the stub into “all streaming is unsupported.”

## Cleanup stays in a separate ownership domain

`wfdDestroySource` at `0x25114` validates driver/source objects, locks the device and calls `0x24fe0` with decrement -1. That helper finds the source's tracking entry, adjusts its reference count at offset `0x10`, and enters its release path only at zero (`0x250a4..0x250bc`). This establishes local reference-counted source release. It does not delete the cluster's RIC PiP resource, acknowledge removal on Ethernet, or prove windshield disappearance.

The earlier controller method-8 disposal and HMI redirection cleanup are separate from this WFD lifetime. A test must close all actually used domains, not substitute one destructor for the others.

## Consequence for V2 and the next test

We now have a traced local output implementation and the second port's packing/callback contract. The live snapshot still shows that output with no windows/scene, while the factory guidance capture uses structured Ethernet models. No retained call or configuration yet connects this packed transmitter output to the Supra's B006 PiP resource and physical windshield.

Therefore:

- Do not create a window on display 2 and label it a windshield test.
- Do not change display coding, transmitter mode, factory window 1056 or installed V1 to force the hypothesis.
- Do not append the 21×1 metadata block to an Ethernet PiP descriptor; that descriptor has no established pixel payload.
- Do not schedule another generic capture trip. The next necessary evidence is a source/receiver binding between this physical video output and the reference cluster, or a different verified pixel channel. Trace retained controller/HMI routing and receiver documentation before proposing hardware work.

A meaningful future larger-display test must identify its producer, actual windshield binding, owned resource IDs and bounded removal. This turn did not establish those end-to-end requirements; there is no live larger-display executable advertised as ready.

## Reproduce and identities

```sh
python tools/verify_output_driver_contract.py \
  --config /private/capture/libwfdcfg.so.0 \
  --driver /private/capture/libWFDomap5430ES2_0.so
```

Dependencies: pyelftools and Unicorn. This tool executes bounded ARM routines in an emulator, never the OEM binary as a host executable. No network/device API is provided to it. Validation: five port-selection cases, exact port-2 table, sixteen mode-conversion cases, three stream-stub cases, and altered-input rejection. This validates only those routines and arguments, not live rendering.

- `libwfdcfg.so.0`: `e244a9cf9285abe50f1856056ef51a0be39cda3ddaf2f60493ff4ec87d9041b4`
- `libWFDomap5430ES2_0.so`: `36250e84e7fee61f0b1e793c1f95afeb642eddedc8bc9f0dd38a8e8572a30239`

Private archive retains the executed results, named-symbol inventory, bounded disassembly, screen call-site inventory and reproduction scripts. OEM bytes and vehicle-specific content remain outside GitHub.
