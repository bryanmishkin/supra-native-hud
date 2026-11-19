# V1 clean pre-drawing recovery correction — 19 November 2026

The extended drive left a persistent lockout despite the final worker proving clean withdrawal. The next boot correctly honored that marker, so the tach did not start. All 15 installed baseline comparisons matched before repair.

## Captured cause

Terminal resident event: monotonic 7,009,889 ms, worker start 89, exit status 512. Worker reason `factory_activity_quiesced`, zero frames, cleanup verified, factory activity true, monitor unknown false. The resident classified this as `worker factory activity after clean exit` and persisted `disabled`. This is a recovery-classification defect; it is not evidence that startup files disappeared.

## Correction

Only a valid, clean, zero-frame `factory_activity_quiesced` result with factory activity true and monitor uncertainty false is eligible for rate-limited retry. It shares the existing 2/4/8/30-second capped resource-contention backoff. Every retry still requires the independent factory lease to report acknowledged idle states and no outstanding requests. A retry never grants ownership. Durable fault evidence remains enabled. Active drawing, uncertain cleanup, unknown monitoring, malformed results and unexpected process exits remain failures.

The worker itself and startup wrappers are unchanged. The supervisor is rebuilt with QNX 6.5, checked against captured dependency exports, staged with readback and rollback, and only then is the diagnosed marker archived. Original Gold and 18 November baseline are preserved.

## Verification

The exact saved terminal record passes strict classification. The real resident reaping path accepts the clean zero-frame case but rejects positive frame count, unverified cleanup and unknown monitoring. Without an acknowledged idle lease it still cannot spawn. Broader real-worker recovery and handoff regressions are also run; target restart results are recorded separately after execution.

A successful restart does not establish two-hour endurance. Private packet captures, OEM style files, profiles, fault logs and compiled packages belong in Drive, not this repository.

## Installed candidate

Supervisor SHA-256: `adc7c038f822ed479fe6c001d35a00c802bdd08c9a3c105671a3d1b6070ed3ed`. Target readback matched. All ten bitmap slots were absent before replacement and again before activation. Filesystem protection was restored. The old supervisor and diagnosed disabled marker were archived on target; complete prior package is retained privately. User restart/display acceptance is pending.

## First restart exposed a separate warm-connection failure

The first corrected supervisor did not restore the tach: both gates selected the hook, but the passive stream parser quarantined at 11,520 ms with `capture began midstream`, zero worker starts, no drawing and proven cleanup. The saved connection (port 65496) contains a cluster keepalive and exact outgoing 16-byte reply `ffff000000000008deadbeef01010100`. The existing exception handled the incoming cookie only.

The correction accepts that exact outgoing keepalive only on an untracked flow. It neither establishes a stream sequence nor grants admission; actual drawing traffic without observed connection setup still fails. All 13 captured packets on that connection replay without fault and with admission false. Negative tests retain rejection of a changed message type and missing factory stream history.

Final installed supervisor SHA-256: `78d463e60e399c299aaf38d608d3fd64593c0863cfd7ea88492eba730bc4e0c3`. ARM build/dependency audit passed, all unchanged component checks passed, target byte readback passed, all ten slots absent before/after replacement, filesystem protection restored. Both earlier supervisors and disabled markers are archived. Second owner restart acceptance remains pending.
