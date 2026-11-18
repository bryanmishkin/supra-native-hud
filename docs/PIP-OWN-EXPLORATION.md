# Our own PiP routing exploration

Owner declined author outreach. Do not post the prepared question or contact upstream authors. Continue with controlled local investigation; keep installed V1 and baseline tags intact.

## HUD Gauges pulled and inspected

Pulled `inotbarnacle/ID6_apps_prerelease` package at `d0df14ac6d394bd2bf29caa6cf2dc5b9ab1fe87b`. The 56,014-byte ZIP SHA-256 is `a0bcdf8e5e73fbde7ce40e674b956fbee357428d74b8c8a65aacea97d4a900df`; all five SHA256SUMS entries match. The worker remains `4dde1d9ced76acc4848f2d886be3053eda3f0497805dd148a299416f99c94b4b`, identical to the earlier review.

Its symbols include `draw(HudTerminal&, ...)`, `tachBand(Batch&, ...)`, `Core::next(... most::Msg&)`, and `HudTerminal::attach(most::Client&, ...)`. The package targets the N18032I reference 340i, and the public README limits testing to F3X. The public source tree does not include this worker's HUD drawing source. The MOST backend is not a Supra Ethernet PiP implementation. We did not run or install the package. Preserve its bundled license and notices; do not apply the dashboard source's MIT license to the packaged worker.

Sources: [package](https://github.com/inotbarnacle/ID6_apps_prerelease/blob/d0df14ac6d394bd2bf29caa6cf2dc5b9ab1fe87b/packages/hud-gauges.zip), [compatibility instructions](https://github.com/inotbarnacle/ID6_apps_prerelease/blob/d0df14ac6d394bd2bf29caa6cf2dc5b9ab1fe87b/AgentReadMe.md). Credit inotbarnacle; no third-party implementation copied into our application.

## Exact comparison now available

`tools/audit_pip_binding.py` reads an existing PCAP and produces a chronological record of B009 sink events, known method-3 native-resource requests and method-11 detailed-model high-guidance references. It records flow, client/session, timestamp and packet hash. It neither connects nor draws; unknown layouts are not guessed. Requests are not ACKs or proof of acceptance.

Replayed against the retained factory capture and failed revision-2 marker:

- Failed marker: resource `0x02000004`, 320×200, depth 0/packing 0; detailed-model high-guidance reference also `0x02000004`. No B009 selection. This rules out a mismatched ID in those two transmitted fields, not an unbound stream at the receiver.
- Factory capture: two 460×237/selection-1 events and completions; one matching detailed-model request has high-guidance reference `0xffffffff` (absent). No native-resource request in the exact supported shape. Other variants and preexisting state are outside this decoder's coverage.

27 focused PiP tests pass. The new tests cover known serialized bindings, truncation, inconsistent IDs and rejection of unknown variants. These are parser checks, not a receiver simulator.

## Next controlled experiment: factory route change

This is a prepared investigation design, **not a ready custom drawing fix**. Before scheduling the session, assemble the current capture runner and exact readback commands into one kit and verify its bounds. The retired marker runner remains disabled.

Question: does the ordinary factory HUD navigation setting cause a different DisplaySink selection or native image binding? Existing captures of route start do not answer that question.

While parked, use an already active factory route and record continuously through these phases. Record the original menu state first. Only use an exposed normal HUD/navigation display setting; do not change coding or assume a menu exists.

1. 20 seconds with the original factory navigation display state.
2. 20 seconds after turning the normal HUD navigation display option off, if available.
3. 30 seconds after turning that same option on; owner identifies the windshield content independently of the cluster.
4. Restore the original option and record 20 seconds of return.

Use the existing bounded passive recorder for B006/B009 and service discovery, plus synchronized factory logs and the already established Screen/LayerManager readbacks at each phase. Pause the V1 worker using the proven procedure only if needed for observation; do not replace its files or startup. Preserve timestamps and do not claim simultaneity between host markers and head-unit packets without clock alignment. Capture counters, drops and readback success must be retained.

Interpretation:

- New selection 0 plus a native resource/reference: extract the exact factory sequence and compare metadata/output state before preparing custom pixels.
- Selection changes but no native reference: routing and pixel supply remain separate; inspect the associated factory model variant rather than assume completion activates video.
- Only vector/navigation models change, with selection 1 unchanged: that menu does not exercise the PiP windshield path. Do not repeat the same test or turn that result into a claim that the hardware cannot do it.
- Menu unavailable: skip the toggle; do not improvise coding changes or send a guessed sink request.

Before any future active subscription experiment, resolve endpoint ownership and restoration. A second subscription from the factory HU address may affect the factory route. Do not bind the factory discovery listener, invent an address alias, or fabricate a selection-0 notification. The eventual test must use the real receiver's selection and verify both remote withdrawal and local window removal.

Exit with original menu state restored, V1 updating, original V1 hashes unchanged, no experimental window/resource remaining, and all evidence saved. No car connection occurred during this preparation.

## Executable capture kit (18 November)

`tools/pip_exploration.py` now implements before/after V1 hash checks, four timestamped factory-state snapshots and an offline completion audit. Use the supplied private kit's `RUNBOOK.md` and hash-pinned recorder. V1 stays running; no custom producer, SD subscriber, layer setters or persistent writes are included. Capture runs independently for 120 seconds and removes its RAM executable afterward. The recorder and snapshot readers use separate manifests.

The four phase holds are 20/20/30/10 seconds minimum. Record the owner's actual observation and original menu value. Do not imply that a menu toggle is already known to select PiP. If the normal factory option is absent, skip this experiment and preserve that result; do not change coding or invent routing commands. A missed phase, unreadable snapshot, packet gap/drop, hash mismatch or unverified cleanup makes the evidence incomplete. A technically complete capture still requires the owner's final restoration check and does not prove larger windshield pixels.
