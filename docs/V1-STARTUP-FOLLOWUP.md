# Startup follow-up — 17 November 2026

The earlier accepted shutdown/start record is one successful cycle, not proof of reliable cold startup. A subsequent boot initially showed no tachometer and later recovered. Its saved Ethernet capture contains eight TCP SYN requests to internal gateway 160.48.199.16:6801 answered by RST/ACK before a successful connection and RPM replies. The first saved successful run begins around 193 seconds of head-unit monotonic time. PCAP wall time changes during clock synchronization; do not subtract its first packet timestamp across that jump.

A further controlled startup remained blank after five minutes cable-free, car-end-only ENET insertion, and laptop connection. Retrieval found a different definitive blocker: persistent `disabled` = `worker startup deadline`, terminal record `QUARANTINED: worker startup deadline` with `cleanup_proven=true`, and both gates reporting `persistent-disable-present`. All 15 installed payload/config comparisons matched the accepted repair. This trial cannot determine cable dependence because the app was disabled throughout it.

## Reproduced defect and correction

The resident checked for a missing worker control socket more than three seconds after fork even after admission. A running worker can remove that socket during clean RPM-failure teardown before the parent observes process exit. The old code then falsely quarantines and persists the startup deadline, blocking the next boot.

The startup watchdog now applies only before admission. Reaping and verified result/cleanup continue to govern admitted workers. Uncertain cleanup still quarantines; this is not a general clearing of disable tokens.

`tests/resident_startup_deadline.py` reproduces the exact quarantine with old source after a healthy >3-second run, clean input failure and a delayed exit. Corrected source recovers cleanly; a child that genuinely never starts still triggers the deadline.

Deployment requires exact installed hashes, stopped app, the exact saved fault plus cleanup proof, and two read-only empty-resource checks. Only the supervisor changes. Preserve the fault token in an archive after validated replacement, keep enable/startup/worker/profile unchanged, and restore read-only protection.

Live validation pending. Earlier gateway rejection/delay remains a separate question; do not claim this watchdog correction proves cable-free gateway readiness.
