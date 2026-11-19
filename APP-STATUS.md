# Verified application status

**19 November update:** the extended drive exposed a clean pre-drawing factory-event lockout. A corrected supervisor is installed; owner confirmed V1 visible and updating after the second restart. The worker and startup wrappers remain the 18 November versions. See [recovery evidence](docs/V1-ADMISSION-RECOVERY-2026-11-19.md). The earlier drive below remains historical evidence.

Current V1: **`v1-baseline-2026-11-18`**, installed and enabled on the reference Supra. [Exact component hashes, private package and limits](docs/V1-BASELINE.md) are authoritative.

| Item | Current evidence |
| --- | --- |
| Final worker startup | Owner confirmed tach visible after iDrive restart; installed hashes verified. |
| Latest drive | Owner reported no visible tach loss; all 15 post-drive comparisons passed. |
| Runtime health | Seven worker starts, six clean factory handoffs, no quarantine, advancing frames. Not one uninterrupted worker run. |
| Recovery/faults | Current input/pool retry counters zero; no permanent fault record changed during the passing drive. |
| Factory image coexistence | Worker checks only its two slots; actual-worker tests preserve occupied factory slots 0..7. |
| Permanent logging | Target write/read proof and byte-identical record after restart; earlier drive failures successfully captured. |
| Native RPM | Factory EngineSpeed2 through DSI/MOST; diagnostic gateway no longer supplies persistent runtime RPM. |
| Display | Existing V1 150 × 36 smooth, symbol-free sport layout with corrected colors; no V2 or boost installation. |

One reference vehicle/firmware only. Repeated overnight starts, extended endurance and all warning/assistance scenarios remain unverified on this exact final build. Earlier cold-start and navigation/radio trials remain dated evidence, not universal guarantees. The original Gold tag is preserved as historical.

See [latest drive](docs/OWN-SLOTS-DRIVE-RESULT.md), [architecture](docs/APP-ARCHITECTURE.md), [operations](docs/OPERATIONS.md), and [historical index](docs/INDEX.md). Do not let older candidate/pending/diagnostic-gateway statements override this current baseline.
