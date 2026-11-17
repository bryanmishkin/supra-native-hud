# Accepted V1 startup repair — 17 November 2026

The reference Supra passed an owner-operated vehicle shutdown/lock and normal start with ENET unplugged. The tachometer appeared automatically and updated smoothly. Subsequent machine evidence established a fresh startup, matching installed files, navigation/radio cleanup and automatic return, healthy live RPM, enabled persistence and read-only filesystem protection. The app was left running.

This supersedes the earlier pending/failed candidates in the [investigation record](V1-COLD-START.md). Gold Master remains an unchanged historical tag; its startup behavior is not the current accepted implementation. V2 remains separate and must incorporate these V1 runtime fixes before deployment.

## Exact implementation

Executable source through `2f1e724`; `4e6e475` adds tests/documentation without executable changes. Private accepted package is the session's `readiness-kit/patched-reference`, with full baseline and staged repair evidence retained. It is an exact installed-file reference, not a generic fresh-car installer.

| Component | SHA-256 |
| --- | --- |
| Resident | `a4ec53d3f83f0fe6cf1890ca03c8a1404f0c3a6c9f83166ebd7785853bcb15ac` |
| Worker | `78e9f6d959a10ca8084360148899a96d34032027ba5fc2ea4eb50e4211f401b6` |
| Navigation gate | `bc8664099f5685f63b062fda67833cd8e5686fe90163867a38d3177fe66c3279` |
| HMI gate | `39b10dcce62c61008b7ec9bfc1ffa99f4ad3dfd066645144bcaf64a756887817` |

Rendering, profile, shared-session ownership and factory startup configurations retain their accepted V1 behavior. The runtime repairs add: internal RPM source/gateway `160.48.199.119 → 160.48.199.16:6801`; verified-clean input recovery with 1/2/4-second backoff then at most one attempt per 30 seconds; 500 ms drawing ACK allowance with unchanged 300 ms RPM freshness; boot-local handling of factory connection closure only after proven clean withdrawal; and bounded startup/fault diagnostics. Uncertain drawing transport or removal still quarantines.

## Live evidence and owner observations

| Check | Evidence |
| --- | --- |
| Cable-free normal start | Owner: “The tach came on automatically and is updating smoothly.” No iDrive reset was used for this start. |
| Fresh startup and exact files | `23-cold-success-navigation`: fresh runtime evidence, both gates selected hooks; all 13 payload comparisons and both factory startup files matched; no disabled token. |
| Navigation takeover | Owner confirmed normal navigation in both displays and tachometer gone. Latest 79-frame worker reports `factory_navigation_request`, cleanup true, shared instance preserved; supervisor not quarantined. |
| Navigation return | Owner confirmed return. `24-final-radio-return` shows live frames 44 → 53; initial radio action was not counted as machine-verified because no radio-active event had yet been captured. |
| Explicit radio takeover | `25-explicit-radio`: radio-active commits observed; 38-frame worker cleanup true; owner confirmed normal HUD selector and tachometer gone. |
| Radio return and final live state | `26-final-running`: worker running, six worker starts, five clean stops, navigation idle/active commits 5/13, radio idle/active commits 5/14, no quarantine. Frames 32 → 41, RPM 654.5 → 656.0. Owner confirmed smooth tachometer with no unwanted graphics. |
| Persistence/protection | Enabled token exact; `/fs/sda0` reports `rdonly`; process arguments show the internal gateway route. Left running, not rolled back. |

The second lock interval began at 18:50:59 UTC. The owner elected to start sooner than the proposed ten-minute interval, and start was authorized at 18:55:47 UTC; actual engine-start time was not measured. Do not label this a completed ten-minute wait. Elapsed waiting alone does not establish sleep: the subsequent runtime evidence establishes a fresh head-unit startup, not electrical sleep of every vehicle module.

## Offline verification and limits

251 Python tests pass. Native integration passes normal handoffs/return, zero-frame cold RPM unavailability beyond the old retry cutoff, malformed input recovery, delayed correlated ACK with stale-RPM cleanup, fresh two-lane admission, pre-admission takeover, clean factory closure, and persistent quarantine for uncertain drawing cleanup. QNX ARM build and static dependency/import audits pass.

This is one verified repaired shutdown/start cycle and parked acceptance on the reference vehicle/firmware. Repeated overnight cycles, long road endurance, full stop-start coverage and other vehicles are not established. Keep the original Gold installer state and factory configuration originals for rollback. Do not treat historical `last-resident.status` text as a current fault without fresh runtime state and the actual disabled-token state.
