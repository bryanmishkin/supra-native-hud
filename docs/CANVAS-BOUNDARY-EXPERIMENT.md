# Parked canvas boundary experiment: falsifiable test, not another inventory

**Created 19 November 2026. NOT performed on the vehicle.** Experimental host runner: [`tools/run_canvas_boundary_trial.py`](../tools/run_canvas_boundary_trial.py). Its default is no network. Working V1 installed binaries/configuration remain unchanged.

## Question this actually answers

Can the **same B006 road-icon bitmap transport and known visible navigation graph used by V1** accept and **project a bitmap taller than 150x36**? The original V1 has already served as a positive control on this car. Unlike registry searches or merely inspecting a 320x320 configuration, this produces an unmistakable visual result if the larger region is actually rendered.

It does **NOT** answer whether the *whole* windshield is independently addressable, and a rejection cannot disprove all other drawing paths. The runner must never label `full_canvas_proven` true based only on an acknowledgement.

## Confirmed and eliminated assumptions

- Vehicle-verified V1: B006 at 160.48.199.96:30502, shared factory handle 200; bitmap **resource type 1**, method 3/variant 2, **150x36**, RLE32. Visible binding is method 14/coming-road model type 40. See [RLE32 live proof](../RLE32-LIVE-PROOF.md).
- The **same captured handle-200 configuration** offers a 320x320 maximum **PiP resource type 2**, configuration tag 35, IDs 0x02000000..04. This does not establish a user-writable bitmap.
- Actual captured controller serializer: `0xBB51E8 -> 0xBB5158 -> 0xBB50C0 -> 0xBB501C -> 0xBB4F84` leads to dimension/enum writers; **the traced PiP variant-3 chain does not use the bitmap pixel-byte-array writer `0xBB58D4`**. Bitmap variant-2 reaches that writer through `0xBB6350`. Conclusion **limited to the traced sender**: PiP variant 3 is not a drop-in carrier for V1 pixels. A distinct PiP source or display attachment may still exist. See [resource parity](V1-PIP-RESOURCE-PARITY.md) and the separately packaged offline ARM proof gate.
- The 800x480 and 480x431 GVCommand PiP records describe factory **source-stage graphics descriptors**, not proved windshield pixel dimensions. Their role still requires identifying `setPIPElementForICHUD` and `sendAttachToCommandPIPICHUD`.
- The factory HUD-height adjustment rectangle observed 18 November is *not* the earlier custom rectangle/cross. Optical HUD-height movement alone is not evidence of programmable custom X/Y.

## Ready test and expected outcome

The host-side experimental runner is isolated from the installed worker. One run uploads a white-bordered rectangle/cross in exactly **one** explicitly chosen larger size: `150x48`, `150x72` or `150x144`. It uses the already-live-proven V1 graph, but does **not** modify on-car V1 executable or configuration.

### Safety/admission gate (must be satisfied before any upload)

1. Park with the windshield HUD functioning, with navigation and radio selector stopped. Do not run on a moving vehicle or with assistance/warnings needing HUD priority.
2. Retain current faults and working V1 evidence. The **owner/operator must separately initiate the installed resident's cooperative boot-local stop** (not `persistent_install.py disable`, which creates a persistent disable marker):
   `ssh -S "$SSH_MASTER" root@"$HEAD" '/var/opt/supra-hud/v1/supra-resident-qnx --stop /tmp/supra-hud-v1'`
   It must print **CLEAN**. The observed resident implementation handles STOPAPP1 by exiting for this boot. Normal subsequent factory startup is expected to start V1 again; this still requires verification.
3. Before opening any cluster connection, the experimental runner itself checks for absent factory broker socket; exact STOPPED status; `cleanup_proven=true`; no persistent `disabled` marker; and no worker process. These checks fail closed.
4. The live runner's existing `SharedSession.preflight` requires the *entire advertised type-1 bitmap resource pool* absent before writing. It never disposes the factory instance or uses PiP resource IDs.
5. The operator must supply exact archived `profile-probe/001-response.bin` and `navigation-cycle/recording-7740ddd3/stream-007.bin` from the private November 16 archive. The runner validates the shared handle/profile and required support models. No guessed profiles, endpoints, or factory image reuse.

### One bounded parked test

Dry-run preflight (no network):

```sh
python3 tools/run_canvas_boundary_trial.py --canvas-dim 150x72
```

After all safety gates, the operator may explicitly execute this from the existing source checkout, with verified current SSH master/head address and saved private files:

```sh
python3 tools/run_canvas_boundary_trial.py --execute \
  --canvas-dim 150x72 --v1-stopped-clean --guidance-stopped \
  --window-seconds 10 \
  --create-response "$PROFILE_REPLY" --support-stream "$SUPPORT_STREAM" \
  --ssh-socket "$SSH_MASTER" --head "$HEAD" --output "$NEW_RESULT_DIRECTORY"
```

The operator records whether **both the top and bottom border of the taller marker are visible in the windshield**. The 10-second window is bounded, with visual yes/no/unknown captured if an interactive terminal is available. The runner then cancels references, empties the road list, restores stopped factory destination data, disposes only the test image resource and checks that it is absent. It records request/response packets, individual acknowledgements, final cleanup and forwarding removal. Any uncertain cleanup blocks another attempt.

### Interpret outcomes without moving the goalposts

| Observed result | Conclusion |
| --- | --- |
| Upload accepted, resource present, both edges visibly projected in windshield, and cleanup fully verified | **YES:** the existing V1 resource/graph can draw more vertical pixels than 150x36, at least for this size. |
| Upload accepted/present, but image visually clipped at the former boundary | The renderer may allow a taller resource but **the visible road-icon slot/graph is limited**. It does not prove full windshield writable. |
| Upload rejected with a correlated server error, or post-upload resource absent | **NO for this tested dimension in this resource interface**. It says nothing conclusive about independent PiP/other HUD paths. |
| Request timeout, malformed reply, unexpected factory overlay, no visual witness, or unproven cleanup | **INCONCLUSIVE/ABORT:** preserve packets, do not try a second size or infer geometry. |
| Full clean positive test | Keep the evidence, verify factory graphics, then test one next size if still appropriate. Do not install or auto-start the experimental runner. |

If the marker disappears but reported resource cleanup is not proven, the result remains a failed safety gate. If only ACKs succeed but no visual observation is made, it is not a visual pass.

## After testing

Verify normal factory speed, speed-limit, navigation and radio, and the working V1 tach after a normal next startup. Do not rewrite, reinstall, or silently re-enable V1 after a failed experiment. Preserve result packets and any permanent fault records before recovery.

## Separate PiP hypothesis

If the road-icon oversized test is rejected or clipped, *do not replay the same inventory again*. The different candidate is the PiP source/displayable path: fully trace the already captured `sendAttachToCommandPIPICHUD` plus its source attachment, then design a valid ICHUD-specific marker. Because the currently traced PiP resource is a descriptor without the V1 pixel-byte writer, simply changing the resource ID or patching the bitmap sender to type 2 would be an invalid experiment.

**No live canvas experiment has yet been executed.**
