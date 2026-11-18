# Pick up this project

Latest car result: [PiP marker attempt](PIP-MARKER-RESULT-2026-11-18.md). Native producer posted 255 frames, but owner saw only a right-turn arrow—not the custom marker. Resource removal, visual cleanup and unchanged V1 return passed. Both recordings had zero drops and no B009 messages. Do not report a larger windshield image as proven or repeat this candidate without analyzing the retained evidence.

Latest candidate: [30-second native PiP marker experiment](PIP-MARKER-TEST.md). Separate QNX ARM helper and Python controller, selected PiP slot 4, 320×200 marker in an 800×480 native backing, explicit withdrawal/removal and manual verified V1 return. This is a prepared hypothesis test, not proven windshield output. Read its admission and failure handling before any live use. Keep V1 unchanged.

Latest external implementation lead: [ryseek's native G30 PiP source and Supra comparison](PIP-G30-REFERENCE-2026-11-18.md), pinned at `a0242e1`. It supplies the missing concrete secondary-Screen producer pattern and frame envelope, but explicitly pauses for its HUD sink. Preserve the author credit and distinguish G30 geometry from the captured Supra 460×237/selection-1 event. No G30 code or vehicle changes were made by this review.

Latest offline result: [output-driver contract](OUTPUT-DRIVER-TRACE-2026-11-18.md). Port 2 uses a TDA19988 callback path with RGBA-over-RGB width conversion verified by executing captured ARM routines offline. This does not establish its physical windshield/cluster binding; no larger live test is ready. V1 remains unchanged.

Latest completed session: [output-driver capture](OUTPUT-DRIVER-CAPTURE-2026-11-18.md). 65 unique files verified; all 15 V1 comparisons passed, faults unchanged, owner confirmed normal displays. Continue output-driver tracing offline; no larger windshield binding proven.

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
