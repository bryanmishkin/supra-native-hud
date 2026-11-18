# Persistent fault evidence and recovery candidate — 18 November 2026

Status: installed on the reference car on 18 November; permanent-record survival after restart verified byte-for-byte; tach returned and recorded up to 7024 RPM. The old acceleration-failure lockout was archived only after exact baseline checks and two empty-pool proofs. The successful short drive remains historical evidence, not proof of extended reliability.

## Observed failure

On 18 November the engine-off capture found `worker exit/cleanup uncertain` with `cleanup_proven=true`. All 15 installed-file comparisons matched the previous movement kit. Startup gates blocked on the persistent disabled token. The detailed worker result and journal were lost with the RAM filesystem overnight. No new corresponding worker core appeared in the dump index. Thus a clean but unrecognized worker exit is supported; the initiating reason is unknown. Acceleration/redline causation is not established.

## Candidate behavior

The supervisor accepts only the worker's complete terminal record, optionally preceded by known DSI startup lines. It distinguishes malformed/missing results, abnormal process termination, unverified cleanup, monitor uncertainty, factory activity and other unexpected clean exits. It requires normal expected process exit codes and proven cleanup before recovery.

Existing `rpm_transport:*` and `RPM stale` recovery remains rate limited: 1, 2 and 4 seconds, then 30-second intervals; a run lasting at least 30 seconds resets the retry sequence. `invalid/stale RPM` now uses that same path only with verified cleanup and no foreign/unknown-monitor flags. Every new worker must still obtain normal factory admission and fresh RPM. This does not retry unknown drawing errors, ignore monitor loss or delete shared factory resources. Unexpected clean failures remain disabled with an accurate category and the original reason preserved.

Before retrying or ending a faulted resident, the supervisor writes under `/var/opt/supra-hud/v1/`:

- `fault-first.json`: preserved once; never overwritten by normal startup or later faults.
- `fault-recent-0.json` through `fault-recent-3.json`: bounded recent records. Sequence slots restart per resident boot; use record times to order across boots.

Each self-contained JSON record includes event/time, raw wait status, worker start count, cleanup proof, supervisor fault, worker terminal output and stderr, tails of current/previous drawing journals, status/admission snapshots, and captured rejected factory request/reply bytes encoded as JSON strings. Terminal output/stderr are capped at 16 KiB each; journals/status tails at 64 KiB each. Journals already contain RPM/frame/sample timestamps. A tail can begin mid-line; preserve the raw string when analyzing. Status snapshots may precede the final reap, so terminal result/wait status are authoritative for the exit.

Files are written completely to a temporary file, fsynced, atomically renamed and synced. The first failure remains separate from the four recent slots. Repeated recoverable input events with the same reason are persisted at most once per 30 seconds after the initial event; a changed reason is saved immediately, to bound flash writes; quarantine events are always captured. Write failure blocks automatic resume and emits a diagnostic. This reduces shutdown loss but cannot guarantee survival of sudden power loss during a write or failed storage.

`tools/capture_cold_start.py` copies these permanent records before the old runtime inspection. It does not clear them, activate the app, restart iDrive or change configuration. No credentials or captured factory data belong in GitHub.

## Validation and next vehicle session

Offline checks exercise strict outcome parsing, malformed results, uncertain cleanup remaining quarantined, known input recovery, persistent record retention after deleting the RAM state, and rapid valid RPM jumps up to 7700. Values over 7700 remain rejected. No RPM jump-rate rejection exists. Boundary rendering tests do not establish real high-RPM sensor calibration.

The package contains the exact previous worker and a rebuilt supervisor; hooks, artwork, profile, enable state and startup configuration are unchanged. Before deployment, archive the existing disabled token and records, compare the installed baseline, verify the bitmap pool is empty, retain the old supervisor for rollback, replace only the supervisor, verify its readback and restore filesystem protection. Activate only deliberately after those checks. The current lockout must not simply be deleted as part of copying files.

First validate permanent storage on the target with a bounded known input failure and inspect the complete record; confirm it remains after a normal restart. Then use normal driving if needed, with no need to reproduce hard acceleration. If a dropout occurs, inspect the permanent record before any recovery. Do not describe this candidate as a fix for the unknown acceleration trigger.

## Completed offline checks

253 Python tests passed. Existing supervisor/worker integration and startup-watchdog checks passed; retention integration verifies uncertain-cleanup quarantine and input recovery with durable records. The actual supervisor evidence method passed first-record preservation, identical-event throttling, immediate changed-reason saving, RAM deletion/new-instance survival and write-failure blocking. Rapid RPM and boundary rendering tests passed. ARM QNX build and captured-runtime dependency/import audit passed.

Candidate supervisor SHA-256: `1cd996960892f0cc98b64851f177358101ef596e163590526d3b164d849cd793`. Unchanged worker SHA-256: `91191ffed2d15f566bafcf916054cff0c0910c74c88f69c4337b6a87dafe3217`. Not installed or road-validated.

## Installation checkpoint

Exact candidate supervisor was installed and read back, rollback copy retained, and filesystem read-only protection restored. A separate no-drawing probe using the production Resident::evidence method successfully wrote/read permanent JSON on the head unit, removed its synthetic fixture and retained the record under an isolated fault-proof directory. It did not touch the real fault-record files or send HUD commands. Restart survival and live runtime acceptance are pending. Probe source: `tools/fault_store_probe.cpp`.

The subsequent drive captured a clean `bitmap pool in use` stop. See [installed retry correction](BITMAP-POOL-RETRY.md).
