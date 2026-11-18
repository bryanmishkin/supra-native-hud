# Own-slot startup admission — 18 November 2026

Installed on the reference car; restart verified; next-drive validation pending. Worker SHA-256 `5be8a000f7d8d0561a3c7b1d2043d1be5bce88af5d68cbc66c7be5189f232274`. Supervisor remains `7396aaaf9ddfd58011c5cde875f8f4df332a41bdbad1a1cb984aa7a590446595`.

The previous worker unnecessarily required all image slots 0..9 to be empty. Captured drive failures identified an occupied slot 0 before drawing. The resource encoder permits creating/removing only `0x01000008` and `0x01000009`, and the validated profile binds the tach to those slots. Startup now checks only those two slots. Occupied factory slots 0..7 therefore do not independently block startup. A busy tach slot still returns the same zero-frame clean result to the bounded retry supervisor, and stderr records the exact occupied ID for permanent evidence.

This does not change shared-model ownership or suppress factory takeover. Factory admission, passive traffic guarding, uncertainty handling, image checks during drawing, cooperative cleanup, retries and permanent logging remain. Factory-owned images are neither overwritten nor deleted. This is intended to remove the measured startup suppression; unrelated handoff or warning behavior is not claimed solved.

Offline tests used the actual worker with all eight factory slots populated: it rendered multiple frames, cleaned up its own images, and left every factory image unchanged. Separate occupied-slot-8 and occupied-slot-9 tests sent only read-only presence queries and drew zero frames. The real supervisor/worker busy-slot retry test passed with slot 8 occupied. All 12 existing worker cases passed, including lost ACK, invalid replies, capture uncertainty and cleanup. Native QNX compilation and captured-runtime import/dependency audit passed.

Installation compared the prior package, cooperatively stopped the active tach, verified terminal cleanup and process exit, retained all permanent fault records, verified empty resources twice, retained the previous worker, read back the replacement and restored read-only protection. No factory resources were removed by the installer. Only the worker changed; no startup, profile, hooks or supervisor changes.

Owner confirmed tach visible after restart. All 15 package/config checks match, the supervisor reports one running worker with no quarantine or retries, and the original first-fault record remains byte-identical. This verifies startup of the new worker, not the next drive result.
