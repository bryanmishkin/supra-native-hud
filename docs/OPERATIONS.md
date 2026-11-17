# Operation, evidence and recovery

The installed app needs no Mac, cable or SSH session to display RPM. The owner verified startup after an unplugged iDrive reset. Navigation and radio temporarily take priority; the tachometer should return after their acknowledged idle states. A full cold sleep/wake cycle is not yet established.

## What to save before unplugging

Use the existing verified connection; do not unlock or reconnect to a different device based on a guessed address. `persistent_install.py collect` saves these files from `/tmp/supra-hud-v1` into the installer evidence directory:

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
| `rpm_transport:...`, cleanup true | Classified input transport failure; bounded retries may occur. Persistent outages can exhaust the retry budget and disable the app. |
| `cleanup_verified:false` or uncertain drawing ACK | Removal is not established. Preserve evidence and use known normal restart/recovery; never claim stopping the process cleared the display. |
| Factory normal after restart but no hook | Gate may have fallen back (activation, preload, readiness or private-file checks). Inspect actual startup state before changing it. |
| Warm iDrive restart did not visibly blank HUD | The cluster drives the HUD; its visible continuity alone does not prove the head unit failed to restart. Use boot/process evidence. |

The exact server keepalive on a previously unobserved connection and a reset of an unused startup connection are narrowly tolerated. Resets involving tracked shared traffic, missing packets, uncorrelated replies and uncovered writers remain faults. Do not generalize the boot fixes into “ignore all resets.”

## Recovery boundaries

Use [disable/rollback](../PERSISTENT-INSTALL.md#disable-and-restore-factory-startup). The reference owner's volume/power-knob hold was repeatedly verified to restart iDrive normally; another vehicle needs its own established recovery method. No generic hold duration is promised here.

The hook bounds its wait and ultimately allows factory traffic even when tachometer cleanup is uncertain. Quarantine protects against blind app retries; it does not prove the remote display has cleared. Confirm both windshield and gauge cluster visually and check factory functions after recovery.

The accepted revision's startup, normal handoff, return and parked continuous operation are established. A failure during engine-off, sleep/wake or prolonged driving is new evidence, not proof that the parked results were fabricated or that a retry token should be cleared automatically.
