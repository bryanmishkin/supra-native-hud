# Corrected content-binding tests: no visible custom image

19November2026, parked reference Supra. Prepared source revision `e9943be458074dc3e3ae1f44ee930014ee796a11`. No Hz tests, no persistent V1 changes. This result supersedes any implication that the type8 producer trace guarantees receiver bitmap rendering.

## Observed results

| Case | Owner observation | Protocol outcome |
|---|---|---|
| Carousel content word1,36×36 ruler | No image | Upload present; timed window; exact model restore and image absence passed |
| Carousel content word2,36×36 ruler | No image | Same cleanup passed |
| Unchanged factory Carousel control | Recognizable source icons/text visible | Focus withdrawal and exact restore acknowledged; no resource upload |
| Unchanged factory Entertainment control | Top row96.7/Opalite visible and checked | Exact restore acknowledged; no resource upload |
| Entertainment row0,column1,36×36 ruler | Frequency disappears; list remains | Upload present; exact model restore and image absence passed |
| Entertainment row0,column2,36×36 ruler | Station name disappears; numbers remain | Same cleanup passed |

All custom windows ran30seconds after posting. Both current factory models were captured in this boot. The owner clarified the first two manual actions were station-list activations, not source-menu activation; a later explicit MODE action and its capture established the source-menu snapshot. No historical model was used as live admission. Current B00E create-body SHA matches the prepared profile.

The Entertainment target row was correlated with the captured text resources and owner observation: column1 maps to96.7 and column2 toOpalite. Therefore a blank result cannot be dismissed as an offscreen/unidentified row. Unchanged factory controls render, distinguishing failed custom-resource presentation from failure to focus the entire widget.

## Conclusions and limits

The uploaded bitmap existed according to resource-presence checks. Substituting its ID into the two traced content fields did not produce visible custom pixels. On the station list, it removed exactly the corresponding text. This demonstrates field targeting, **not bitmap decoding, correct format acceptance, or a usable custom canvas**. Acknowledgments are insufficient to discriminate unsupported receiver content type, image representation, or resource binding semantics.

No larger dimension trials ran because neither36×36 binding displayed custom pixels. Repeating blank bindings at128×128 would not measure usable area. No arbitrary root-windshield drawing capability was established. Do not reissue this same four-case matrix as a corrected solution without new evidence.

Next analysis must compare the HMI resource sender's actual wire serialization and RLE32 representation with transmitted requests and examine receiver content-type behavior. The current producer-only trace is insufficient to claim compatibility with this receiver. Preserve successful factory controls as the comparison case.

## Evidence and restoration

Private session directory: `canvas-binding-live-2026-11-19`. Includes current-boot startup capture, passive menu recording, saved factory bodies, text-resource inventory, per-request/reply files, per-case journals and owner observations. Four bitmap tests each passed all six cleanup steps; both factory controls passed four restoration steps. Passive recording was validated and its temporary recorder removed.

V1 restoration status is recorded separately in the final session verification. Do not infer that restart succeeded from this test-results document alone. Installed V1 files were verified before pausing; the normal restart resumes the unchanged installation.

## Additional frame controls in the same session

The one-item Carousel was shown with all four references absent and **no bitmap uploaded**. The owner saw the broad frame with an empty interior. Thus the earlier square/frame is a receiver widget decoration, not proof that the uploaded marker's border rendered.

A second control retained the complete current four-item factory Carousel, including its text, and replaced only its selected icon reference with the 36×36 ruler. The owner saw the frame and factory Presets label/icons, but no ruler. Resource presence and all six cleanup steps passed. Both controls were withdrawn and their exact original model restored.

The owner also clarified a separate target: opening HUD Height shows corner lines around the **whole HUD frame**. This is not the radio popup frame. Its activation, renderer ownership, interior drawing contract and removal must be investigated independently. Neither outline establishes writable pixels inside it.

The advertised 320×320 PiP capacity is a third target. Prior 320×200 native-marker attempts displayed only a factory turn arrow; they did not prove custom pixel delivery or a 320×320 windshield surface. The live session is continuing; V1 remains paused with installation unchanged. Restoration is still pending, not complete.

## Read-only firmware preservation

Seven head-unit boot/manifest files were copied and read a second time byte-for-byte: both 1,621,724-byte boot IFS images, the 262,144-byte Cortex-A15 BIOS packet, and system/car/HMI/bootloader manifests. Both IFS images share SHA-256 `5d4a757bc264861fb48a21fe31a17a6a7b76d2ead598ca37c94e6cfbe2d4db39`. Full file hashes and original paths are in the private evidence manifest. These files supplement the previously captured HMI/controller/navigation/output-driver executables; they are **not cluster receiver firmware or a complete vehicle recovery image**. No firmware write, unlock or flashing operation was performed.

## Full-HUD alignment/control inspection

A fresh 120-second Ethernet capture during owner-confirmed corner-line appearances contained 4,438 packets with zero packet/interface drops. Outbound captured cluster TCP application traffic consisted of keepalives; no drawing/image requests were present. This is coverage of the configured Ethernet filter, not all vehicle buses. System-log recording provided no matching HUD messages.

The captured HMI constructor and a bounded read of its live factory-ID object establish Kombi E0/01; the live registry resolves it to provider 0x5000. The HUDSelection2 function is 0xCA6. A new 120-second passive DSI/MOST observer registered this device-control key, sent zero target GET/SET commands, and retained 1,273 E0 messages with zero drops or malformed messages. Two factory CA6 SET/status pairs were present. Their changed byte exactly matches CDevCarHUD adjustment setter 0xf4a788 (UI value -1 then 0); it does not match setMode at 0xf4a6c0. The earlier owner description of down/up agrees with those bytes; a later description of opening without adjustment must remain separate and does not turn these into proven overlay-only mode transitions.

The observer process and RAM files are removed. All 15 installed V1 comparisons passed and permanent fault files were unchanged. V1 is still paused pending the normal restart and visual/runtime verification; this report is not permission to claim restoration complete.

## Receiver firmware access inspection

The candidate receiver's reported link-local endpoint refused SSH, HTTP and HTTPS connections. A parameterless UDS ReadMemoryByAddress probe returned `7f2313`; a single-byte format/access probe at address zero returned `7f2372` and no bytes. Neither response supplies a memory map or proves that all possible readback mechanisms are unavailable. No diagnostic session change, security-key attempt, upload/programming sequence, reset or firmware write was made. A subsequent F101 response had the unchanged SHA-256 `4406c00b629b281dba5556e98dee448fafbf368a51e8556f99063efb03259af4`.

**Matching cluster/HUD receiver executable firmware remains uncaptured.** The boot IFS, HMI/controller/navigation/driver files and newly preserved NBTCarHU, MOST and CSI_NBT executables belong to the head unit. They must never be relabeled as the cluster receiver dump. The private head-unit boot package is saved to Drive; full live-session preservation continues.

## V1 restoration fault — owner confirmed return

The first owner restart did not restore V1. Its resident recorded `capture began midstream`, zero worker starts and `cleanup_proven=true`, then wrote a persistent disabled token. All 15 installed payload/configuration hashes matched the baseline. The next restart correctly honored that token; neither resident nor worker ran. Asking for that second restart before inspecting the persistent token was an operator error.

Both boot records and the first startup PCAP were preserved. The diagnosed token was archived as `disabled.before-canvas-restoration-20261119`; its contents were verified, state synced, and the existing persistent enabled token verified. No binaries or factory startup files were replaced. A fresh owner restart is pending; restoration is not yet verified. Do not clear a future disabled token without inspecting its distinct fault and cleanup evidence.

After that fresh restart, the owner initially reported no tach, then reported “tac is back” and disconnected ENET. This establishes visible return after the diagnosed lockout was archived, not a measured startup latency or post-return runtime verification. No further connection is required solely to repeat that visual confirmation. All 15 installed file comparisons had matched before recovery; no binaries or startup configuration were modified during recovery.

Recovery lesson: inspect both RAM runtime and persistent `disabled`/gate records before requesting another restart. A persistent lockout survives iDrive restarts. Preserve the specific fault, worker-start count and cleanup evidence first; never treat repeated restarts as clearing it. The captured midstream fault remains an offline investigation item; do not claim the parser defect is fixed.
