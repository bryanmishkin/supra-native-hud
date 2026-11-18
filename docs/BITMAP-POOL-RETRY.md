# Pre-drawing bitmap-pool retry — 18 November 2026

Installed on the reference car; restart/live-drive verification pending. Supervisor SHA-256 `7396aaaf9ddfd58011c5cde875f8f4df332a41bdbad1a1cb984aa7a590446595`. Worker remains `91191ffed2d15f566bafcf916054cff0c0910c74c88f69c4337b6a87dafe3217`. Hooks, layout, profile and startup configuration are unchanged.

## Captured cause

The new permanent logger captured `bitmap pool in use`, normal process exit code 2, zero frames and verified cleanup. The fifth worker's only request was the first startup presence check (`0x01000000`). Four earlier clean handoffs were recorded. The preceding worker finished at 4359 RPM and performed acknowledged cleanup. The slot was empty at post-drive inspection, as were all ten checked slots. The exact factory function owning the slot is unknown. The owner's stability-control-warning hypothesis is plausible but unverified.

## Correction

Retry only a complete, valid `bitmap pool in use` terminal result with zero frames, verified cleanup, normal exit code, and no factory-activity or monitor-uncertainty flags. Retry delays are 1, 2, 4, then 30 seconds. Every attempt still requires normal acknowledged factory admission and the existing complete pool check. Occupied resources are never deleted or overwritten. A successful drawing run resets the busy retry count; admission telemetry exposes `pool_retry_count` independently of input retries.

The integration test also exposed a handoff arriving while a clean exiting worker had removed its control socket but had not yet been reaped. Stop now reaps first and, if the control exchange fails, waits at most 100 ms for a verified terminal result. A missing socket alone never establishes cleanup. Missing/malformed results, uncertain cleanup and unrecognized failures remain blocked.

Permanent first/recent failure records remain enabled and survive retry. Repeated identical recoverable failures are rate-limited on disk; a changed reason is saved immediately. Previous fault records and the disabled token are preserved during installation.

## Completed checks

The real supervisor and existing worker passed a loopback test with an occupied factory image: zero uploads or deletions while busy, bounded retries, no drawing while the factory lane is active, return after free+idle admission, clean stopping and retained permanent evidence. Existing handoff/return and lost-ACK quarantine regression cases passed. Strict outcome tests reject retry when frames are nonzero, cleanup is false, or monitor/factory flags are set. 253 Python tests passed. The QNX supervisor compiled and passed captured-runtime import/dependency checks.

On the head unit: exact prior baseline matched, all ten slots empty in two independent checks, replacement readback matched, rollback retained and read-only filesystem restored. No factory images were removed by the installation. Live acceptance is pending; this is not yet proof that all possible driving dropouts are resolved.
