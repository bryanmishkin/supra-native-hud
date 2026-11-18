# PiP identity consumer and the ID6 HUD reference

Offline continuation after both failed PiP markers. No vehicle contact, V1 runtime changes, or new live candidate. **Pixel delivery is still unproven; this report is not an actual fix.**

## Why other projects can occupy more space

These are different drawing paths, even when they run on NBT Evo:

| Reference | Actual target/path in reviewed material | What it establishes for this Supra |
| --- | --- | --- |
| ryseek G30 native PiP | 620×313 instrument-cluster video, 800×480 backing; pauses when HUD selected | Concrete native producer, not a demonstrated windshield video path |
| ghackt installer / st1ng CarPlay payload | Supra Ethernet guidance models; separate MOST HUDTerminal polygon path on supported F-series | Navigation elements can occupy factory navigation layout; not proof arbitrary pixels can occupy that whole layout |
| inotbarnacle ID6 HUD Gauges | F3X windshield, MOST HUDTerminal 82/00 at node 0101, reference 340i N18032I | A real alternative HUD architecture to study, not a compatible Supra package |
| Our working V1/V2 | Supra Ethernet guidance bitmap path; validated 150×36 custom image | Custom pixels are proven in this particular area; a larger PiP stream still needs its own binding proof |

The broader navigation region contains receiver-rendered arrows, text and lanes. Its visual footprint must not be equated with the size of an arbitrary image resource. A working MOST-based windshield gauge or G30 cluster map is not evidence that our secondary Screen output is physically connected to the Supra windshield.

Sources and credit: [ryseek's pinned implementation](PIP-G30-REFERENCE-2026-11-18.md), [ghackt/st1ng review](CARPLAY-INSTALLER-REVIEW.md), and [inotbarnacle ID6 apps](https://github.com/inotbarnacle/ID6_apps_prerelease/tree/d0df14ac6d394bd2bf29caa6cf2dc5b9ab1fe87b). Preserve attribution to nanaisu/NBT-AAD and contributors. No external implementation was incorporated into our runtime.

## ID6 apps: inspected beyond the screenshot

Pinned repository revision: `d0df14ac6d394bd2bf29caa6cf2dc5b9ab1fe87b`.

- README describes HUD Gauges and explicitly limits HUD testing to F3X. Dashboard panel resolutions and HMI compatibility checks are not windshield dimensions or receiver compatibility.
- AgentReadMe requires a unique MOST HUDTerminal 82/00 at node 0101 for its HUD worker. The package README identifies the reference 340i and N18032I firmware.
- The recursive source tree contains dashboard and MOST diagnostic source but no `hud_shape.cpp`/`hud_terminal.cpp` source. Do not imply the worker's full source was reviewed.
- Downloaded `packages/hud-gauges.zip` for read-only inspection. All five files match its SHA256SUMS. Worker SHA-256: `4dde1d9ced76acc4848f2d886be3053eda3f0497805dd148a299416f99c94b4b`.
- The retained worker's symbols identify `nbt::hudterm::HudTerminal`, `hud_shape.cpp`, `hud_terminal.cpp`, and MOST/DSI client functions. Its command-name strings include ImageGetSize, ImageAddPolygon, ImageAddCircle, FrameAddItem and ImageRemoveAllItems. These corroborate the documented transport, but strings alone do not prove which commands execute for each frame or establish the actual canvas dimensions.
- No installer, package executable, ECU command, or external script was run. Original package license and notice are retained in the private evidence archive. The HUD package uses PolyForm Noncommercial terms; do not assume the dashboard source's MIT license covers it.

## New concrete identity-consumer trace

Captured controller identity remains `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`.

Following the previous three-word `[manID, HMI RIC ID, IC RIC ID]` notification found:

1. Thunk `0xa3dc64` adjusts its owner by `0xfc`, then branches to `0xa75104`.
2. Consumer `0xa75104..0xa7518c` checks the HMI identity at notification +4. If it is not `0xffffffff` and owner +0x6c is non-null, it calls that object's virtual slot 0x30 with the maneuver ID. A null lookup result skips the setter. Otherwise it passes the HMI identity to the result's virtual slot 0x20.
3. The second branch independently checks notification +8 and owner +0x70, and does the same for the IC identity. It does not fall back to the HMI identity when the IC branch is absent.
4. The previously identified PiP displayable-session table `0x10574b0` resolves slot 0x30 to `0xa7c464`, which forwards to its task +0x20, virtual slot 0x28. For the PiP task table `0x1058f00`, this is `0xa84f1c` (job lookup). The PiP job table `0x105d748` resolves setter slot 0x20 to `0xaa14dc`.
5. Setter `0xaa14dc` stores the RIC identity at job +0x150. If the guidance-session ID at +0x28 is present, it issues the previously traced content/attachment operations. This resolves a concrete route from the branch-specific ID toward attachment, **conditional on those concrete session/job types being present**. The failed test captures do not establish these runtime object assignments.

`tools/verify_pip_identity_consumer.py` executes the real consumer instructions with observed virtual-call boundaries. Seven cases pass: both identities, HMI only, IC only, neither, no sessions, no jobs, and missing HMI job. Tests confirm which identity reaches which setter and when calls are skipped. The job-lookup return and setter are boundary substitutes, not implementations of the cluster; no physical receiver acceptance is tested.

```sh
python tools/verify_pip_identity_consumer.py /private/NavNBTEvoController
```

## What this changes

Missing session/job binding can explain a producer that posts images without delivering the expected custom image, but it is **not yet the diagnosed cause** of our two failures. Our matching header/model IDs and accepted B006 messages cannot establish these object bindings. Nor does this justify adding factory-internal attachment calls to the live test without proving their ownership and effects.

No next car visit is requested. The next offline edge is the actual session construction/registration and selected job lookup, reconciled with the retained factory model traffic. If that evidence does not identify the physical receiver contract, state the missing edge precisely rather than relabeling another guessed parameter change as a repair.

See [previous binding execution](PIP-RECEIVER-BINDING-2026-11-18.md) and [failed revision-2 result](PIP-REVISION2-RESULT-2026-11-18.md). V1 stays intact.
