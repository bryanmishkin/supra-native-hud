# Pick up this project

Next prepared session: [batched output-driver capture](OUTPUT-DRIVER-CAR-CAPTURE.md). Offline-tested read-only runner; V1 unchanged. Review newly captured configuration references before unplugging.

Latest offline PiP result: [metadata image, identified HMI consumer, disposal and external source review](PIP-METADATA-AND-CONSUMERS-2026-11-18.md). The 21×1 metadata codec matches captured ARM execution; larger windshield routing remains unproven. V1 is unchanged.

Start with [current V1 baseline](V1-BASELINE.md) and its [machine-readable hashes](V1-BASELINE.json). The reference car is installed and enabled; the owner unplugged after a no-visible-loss drive on 18 November. Do not restore factory startup automatically or substitute the old Gold kit.

## Current implementation

Same-PID factory startup gates launch the original nav/HMI programs with the handoff hook and one resident. The resident admits a native worker only after acknowledged factory idle states. The worker reads factory EngineSpeed2 through DSI/MOST and draws via shared cluster Ethernet guidance instance 200, using only bitmap IDs 8/9 in the `0x01000000` namespace. Factory slots 0..7 do not block startup. The profile and hooks retain factory priority; there is no independent windshield surface.

Both factory writers require pre-send coverage. Approved background traffic is authorized byte-for-byte. Actual takeover requests require cleanup. Input failures and pre-drawing owned-slot contention retry only after verified clean exit; uncertainty stays quarantined. Permanent evidence survives shutdown. Read [architecture](APP-ARCHITECTURE.md) and [operations](OPERATIONS.md) for details.

## Evidence discipline

Latest drive: no owner-observed loss, no new fault records, current retry counters zero, six clean handoffs and advancing frames. Do not claim continuous process lifetime, overnight final-build acceptance or universal vehicle support. Prior hard-acceleration correlation did not prove RPM/redline or stability control was the cause; the captured failure was a busy factory bitmap followed by an unnecessary permanent lockout.

The Drive baseline archive named in V1-BASELINE.md contains the exact installed kit, full prior package for rollback, original/after startup configs, source, installation readbacks and drive evidence. GitHub deliberately excludes private profiles, factory bytes, credentials and SDK/license material. A fresh clone is not sufficient to install another car.

## Next work

Preserve working V1. V2 remains separate and needs deliberate integration of final V1 fixes. Prepare and test candidate changes offline before asking for car time. On a new failure, collect permanent records and RAM state before resetting or re-enabling. Do not repeat unrelated navigation/radio tests to investigate a specific input/resource fault. For another vehicle, verify [compatibility](../COMPATIBILITY.md) and obtain its own originals; never reuse this car's rollback configurations blindly.

Current operational docs: [status](../APP-STATUS.md), [architecture](APP-ARCHITECTURE.md), [installation/rollback](../PERSISTENT-INSTALL.md), [operations](OPERATIONS.md). Historical reports are evidence, not current activation instructions.
