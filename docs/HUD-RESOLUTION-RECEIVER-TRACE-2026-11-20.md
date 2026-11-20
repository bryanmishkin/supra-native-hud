# Resolution request: producer routing, not windshield clipping

20 November 2026. Offline only; no vehicle connection or V1 application/startup changes. This is an additional executable check, not a newly admitted larger-canvas test.

## Complete request versus completion

The earlier HMI analysis identified the one-byte completion. The request itself does carry dimensions. In the captured NavNBTEvoController (SHA256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`):

| Native stage | Evidence |
| --- | --- |
| Diagnostic input | `0x886ee4` decodes minimum line thickness, Y, X and display selection; `0x886d74` orders the request as thickness, X, Y, selection. |
| Local request | `0x371208` forwards through `0xcb8cc4` to DNAVNBTMapViewCtrl. Its request fields contain all four values. This is local middleware, not an established B006/B009 wire method. |
| Receiving implementation | Stub dispatch `0xcb7dfc`, derived callback `0x970c9c`, queued record `0x9707b0`, callback `0x96f954`, virtual method +0x30 lead to CGuidanceViewerIcHud `0x6de214`. |
| Actual use | Handler reads only request+0x1c (display selection); it does not read +0x10/+0x14/+0x18 (thickness/X/Y). It updates selection, initializes legacy communication where appropriate, selects a style and may attach a guidance view. |
| View selection | `0x6d71d8` maps local display/view enums to a view ID. `0x6dbbc8` looks up and attaches an existing guidance session. Neither is a demonstrated receiver clip setter. These enums are not B009 HUD0/cluster1. |

A request containing dimensions does not establish that its receiving implementation resizes anything. Conversely, a one-byte completion alone could not have established that the request lacked dimensions. This trace resolves both sides.

## Ethernet gate

The coding callback at `0x6ddb74` calls getter `0x6f453c`. The getter reads internal coding key `0x48800818` and labels value3 `KOMBI_CIC_kombi_ethernet`. That key is **not a verified external diagnostic identifier**.

When the getter returns3, callback `0x6ddbb0..0x6ddbdc` returns before setting coding-available at owner+0xe4. Its own log says `ethernet IC coded, do not start MOST guiding`. The normal legacy branch sets coding-available at `0x6ddd20`. The constructor initializes it to zero.

This gate was already present in older static captures; this pass adds native execution and follows the resolution request all the way to it. The execution uses an explicit coding-value fixture, not a new live coding read. It must not be represented as a measurement of current car RAM. It shows why this legacy path is not a justified resize experiment for the observed Ethernet application services.

## Reproducible native execution

`tools/verify_resolution_selection_contract.py` executes the captured ARM instructions with Unicorn:

- 32 selection/dimension cases, with previous selection0/4 and requested0/1/2/3/4/5/6/255.
- Two dimension tuples per case: thickness1,150×36 and thickness7,800×480. The same selection produces identical intercepted downstream calls. Memory-read hooks verify dimension fields are not consumed.
- The native coding callback and native getter execute with backing coding storage returning3. The callback performs no owner-state writes and leaves coding admission false.
- A subsequent resolution request with coding unavailable performs no style selection, communication initialization or view attachment.

External communication, completion, string operations and logging are intercepted; the test does not emulate the receiver or its pixels. Unknown native targets fail the run. The coding-enabled selection cases deliberately exercise legacy behavior and are not evidence that those states are reachable in the Supra.

```sh
python3 tools/verify_resolution_selection_contract.py \
  --controller /absolute/private/NavNBTEvoController \
  --output /absolute/private/resolution-contract.json
```

## Consequence for the requested larger canvas

Do not send this diagnostic to enlarge the HUD, change cluster coding, force a display enum, or change V1. It supplies no established windshield width/height control.

The photographs still establish two facts: custom resource pixels reach the narrow road-list area, and the complete narrower second panel fits alongside it. They do not establish new vertical extent. Factory finish-flag/distance below the first image is not custom drawing there.

The remaining candidate must belong to the Ethernet receiver path: a receiver-owned layout/clip setter or a separately windshield-bound pixel target with proven removal. No such setter or attachment is established by this result. No repeat strip, alignment, menu-cell or Hz case is added. Actual cluster receiver firmware remains different from the captured head-unit producer executables.

V1 installed files remain unchanged. At the latest session the owner explicitly deferred V1 runtime restoration; this offline analysis does not change or verify that runtime state.
