# Operation, evidence and recovery

[Current V1 baseline](V1-BASELINE.md) is installed and enabled. No laptop is required. The exact final build has restart and one no-visible-loss drive evidence; do not substitute earlier cold-start acceptance for repeated testing of this final combination.

## What to save before unplugging

Prefer the read-only `tools/capture_cold_start.py` collector with the exact current private kit and verified SSH socket. Despite its historical name, it also captures a running or failed drive. It first copies persistent `fault-first.json`, `fault-recent-0.json` through `fault-recent-3.json`, activation/gate state and resident status, then RAM logs and all 15 installed/configuration comparisons. Use a new output directory each time. It neither resets nor reactivates the car.

`persistent_install.py collect` is the older narrower collector; it saves these RAM files:

- `acceptance.json`: uptime, worker starts, clean stops, active/idle commit counters, availability/quarantine.
- `worker.starts`, `worker.result`, `worker.stderr`, `last-result`.
- `active.jsonl`, `previous.jsonl`, `hook.log`, `resident.status`.

Also retain `heartbeat`, bounded `startup.pcap`, release token state, both factory process identities and mapped-hook evidence, exact current startup/configuration hashes and `/fs/sda0` read-only status. These additional checks are not all performed by `collect`. Save each checkpoint separately; RAM state is reset on restart and bounded logs/previous-worker files are overwritten. The current worker's result may be empty until it exits; use its advancing journal and status for live health.

Keep `installer.json`, kit manifest and exact original/after configuration images together. Record source commit, binary hashes, target identity, phase timestamps, actual user observations, and failures as well as passes. Separate machine evidence from visual confirmation and from inference. Do not place factory files, profiles, packet captures or credentials in GitHub.

## Interpreting a missing tachometer

| Observation | Meaning / next step |
| --- | --- |
| First 30 seconds after resident startup | Deliberate minimum settling period. Still needs both acknowledged idle states afterward. |
| Navigation or radio active | Expected yield. Do not force drawing over it. |
| `available:false`, not quarantined | One/both lanes unknown/active or requests pending. Inspect captured commits; silence is not idle. |
| `available:true`, no child briefly | Coalescing/readiness/retry delay may apply; inspect timings and result. |
| `disabled` exists / `quarantined:true` | Automatic operation stopped. Read the first fault and worker cleanup result; do not remove the token as a fix. |
| `rpm_transport:...`, cleanup true | Classified input transport failure; bounded retries may occur. After initial 1/2/4-second backoff, clean input failures wait 30 seconds between attempts; they do not disable an otherwise healthy supervisor. |
| `bitmap pool in use`, zero frames and cleanup true | Only tach slots 8/9 are checked in the current worker; retry with bounded backoff. Permanent records retain the occupied ID in stderr. Do not delete occupied images. |
| `cleanup_verified:false` or uncertain drawing ACK | Removal is not established. Preserve evidence and use known normal restart/recovery; never claim stopping the process cleared the display. |
| Factory normal after restart but no hook | Gate may have fallen back (activation, preload, readiness or private-file checks). Inspect actual startup state before changing it. |
| Warm iDrive restart did not visibly blank HUD | The cluster drives the HUD; its visible continuity alone does not prove the head unit failed to restart. Use boot/process evidence. |

The exact server keepalive on a previously unobserved connection and a reset of an unused startup connection are narrowly tolerated. Resets involving tracked shared traffic, missing packets, uncorrelated replies and uncovered writers remain faults. Do not generalize the boot fixes into “ignore all resets.”

## Recovery boundaries

Use [disable/rollback](../PERSISTENT-INSTALL.md#disable-and-restore-factory-startup). The reference owner's volume/power-knob hold was repeatedly verified to restart iDrive normally; another vehicle needs its own established recovery method. No generic hold duration is promised here.

The hook bounds its wait and ultimately allows factory traffic even when tachometer cleanup is uncertain. Quarantine protects against blind app retries; it does not prove the remote display has cleared. Confirm both windshield and gauge cluster visually and check factory functions after recovery.

Use the exact baseline evidence scope, not older acceptance wording. A failure during engine-off, sleep/wake or prolonged driving is new evidence, not proof that the parked results were fabricated or that a retry token should be cleared automatically.
