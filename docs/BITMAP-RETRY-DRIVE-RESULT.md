# Bitmap retry drive result — 18 November 2026

Owner returned parked with ENET connected and iDrive unchanged. Read-only capture; no reset, token changes, drawing commands or installation.

## Machine findings
- No current disabled token; supervisor not quarantined, worker running in both snapshots.
- First snapshot: 14 worker starts, 4 clean stops. Second snapshot: 15 starts, 5 clean stops. This was not one uninterrupted worker run.
- Four retained recent records are clean pre-drawing `bitmap pool in use` exits, at monotonic times 308124, 338186, 368261 and 398336 ms. They span 90.212 seconds, approximately 30 seconds apart. Each reports zero frames and verified cleanup, with no factory/monitor uncertainty flags.
- Those records show pool retry count capped at 4 and input retry count 0. The current admission snapshot reports both counters 0, no pending factory requests and normal admitted drawing availability.
- Latest completed worker reason is `factory_navigation_request`, 27 frames, verified cleanup. The event name denotes the app's factory handoff path; it does not establish that the owner manually started navigation. The subsequent worker is rendering frames with current RPM values.
- All 15 binary/configuration comparisons match the installed retry package.
- Original first-fault record is byte-identical to its pre-drive copy. No new permanent quarantine appears. Recent stderr files are empty.

## Interpretation
The measured pre-drawing contention now waits and recovers rather than permanently disabling the tach. However, retained evidence shows repeated contention across at least a 90-second interval; this is not dropout-free driving acceptance. Four rolling records do not reconstruct every earlier retry. Whether the owner noticed each disappearance remains to be confirmed separately.

The factory feature occupying the bitmap is still unidentified; stability-control attribution remains a hypothesis. The next improvement should address unnecessary suppression caused by the whole-pool availability check while preserving ownership of factory resources. Do not delete occupied slots or infer permission to reuse them. This capture makes no source or vehicle behavior change.
