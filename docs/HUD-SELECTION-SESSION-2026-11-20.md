# Targeted receiver-selection session

The paired test is packaged with a resumable session runner. No Hz tests, persistent installation changes, coding changes, or factory-process termination. V1 remains the exact current 15-file baseline. The car is not needed for further kit preparation; physical destination selection and visible pixels still require the car.

This tests a specific unresolved receiver decision. It does **not** promise that the larger windshield path is fixed. The known control draws in the cluster. The contrast changes numeric guidance distance from 461 to 69 while preserving image, geometry, support fields, and removal. See [native evidence and interpretation](HUD-SELECTION-TEST-2026-11-19.md). If both select cluster1, the tested threshold hypothesis is rejected; do not repeat it as a new repair.

## Prepared private kit

`outputs/hud-selection-session-2026-11-20` contains the hash-pinned native producer, proven 120-second passive recorder, private profile/create reply, both plans, and an initially unstarted session journal. Private files/binaries are archived to Drive, not committed to GitHub. The source runner is `tools/run_hud_selection_session.py`.

Producer SHA256: `2546bcc83ce396ec3c67df3b5cac8333a9a1f79009b8bb54e06251633efc1753`.
Recorder SHA256: `fc0ee3c1c275ba75dd3ee64402e5b4747d5e7a3454e34c1c318d83df2e045ea6`.

Allow **10–15 minutes parked**, including V1 pause, two full 30-second visible windows, their recordings, owner observations, normal iDrive restart, and read-only final verification. SSH must already be accessible through a verified master connection. The runner does not activate SSH or reboot iDrive.

## Operator sequence

From the repository root, set the absolute kit directory and the current verified SSH master socket. Do not reuse an already-attempted session directory. The packaged directory is unstarted.

```sh
SESSION=/Users/bryanmishkin/Documents/Codex/2026-11-16/referenced-chatgpt-conversation-this-is-an/outputs/hud-selection-session-2026-11-20
SSH_SOCKET=/tmp/supra-canvas-main-ssh
python3 tools/run_hud_selection_session.py pause --output "$SESSION" --ssh-socket "$SSH_SOCKET" --execute
```

Before pause, confirm parked outdoors, engine running, V1 updating, navigation stopped, radio closed. Pause reads/verifies all 15 installed files, saves runtime snapshots, and cooperatively stops V1. Confirm graphics gone from both displays before continuing.

```sh
python3 tools/run_hud_selection_session.py case --output "$SESSION" --ssh-socket "$SSH_SOCKET" --execute --case control461 --displays-clear --guidance-closed
```

Tell the owner to prepare to watch both displays before launching. The runner prints **WATCH NOW** only when the producer reports its visible window started. Native lifetime is independently bounded to 45 seconds, visible time 30 seconds. Each case has its own fresh 0700 RAM directory and TCP forwarding.

The passive recorder starts **before any test resource upload**, records setup, selection, frame posting, withdrawal, and post-test snapshots, and finishes after 120 seconds. These are two continuous per-case recordings, **not one continuous recording across the operator observation gap**. No test traffic occurs in that gap. Packets, native output, direct requests/replies, snapshots, and timestamps are retained. Truncation, drops, early capture exit, missing cleanup, or a failed first case blocks progression.

After the first case, record what the owner actually saw and confirm visual removal. Allowed locations: `windshield`, `cluster`, `both`, `factory-symbol-only`, `none`. A factory arrow is not a custom marker.

```sh
python3 tools/run_hud_selection_session.py observe --output "$SESSION" --case control461 --location cluster --displays-clear --note 'Replace this example with the actual observation.'
python3 tools/run_hud_selection_session.py case --output "$SESSION" --ssh-socket "$SSH_SOCKET" --execute --case contrast69 --displays-clear --guidance-closed
python3 tools/run_hud_selection_session.py observe --output "$SESSION" --case contrast69 --location cluster --displays-clear --note 'Replace this example with the actual observation.'
```

Do not copy example observations as facts. Second case is admitted only after first protocol/local/resource cleanup, complete capture, RAM removal, and owner-confirmed visual clearance. Unsupported sink tuples fail closed and remain evidence; no in-car geometry edits.

## Restore and verify before unplugging

After both tests (or a failed test), preserve evidence and use the established normal volume-knob restart. Confirm V1 visible and updating. Re-establish diagnostic access if restart closed SSH, without another blind restart. Then:

```sh
python3 tools/run_hud_selection_session.py finalize --output "$SESSION" --ssh-socket "$SSH_SOCKET" --execute --v1-visible
python3 tools/run_hud_selection_session.py audit --output "$SESSION"
```

Finalization verifies the same 15 hashes, two healthy supervisor samples, advancing heartbeat **and drawing-frame/sample counters**, enabled/no-disabled token, empty OTHER2, and absence of both private test directories. Failed verification preserves evidence; another attempt writes a new post directory. No lockout is cleared automatically and no V1 component is rewritten. A restart is a manual checkpoint, not simulated by the runner.

`completeness.json` separates completed investigation from a visible windshield result. A negative cluster-only outcome can be a complete investigation. A failed test cannot produce complete status; V1 restoration can still be verified separately. Do not keep the owner in the car just to upload: retain the local evidence, then archive after physical restoration is verified.

## Offline checks and limits

Session gate tests cover truncated/dropped/short recordings, missing cleanup, missing case observations/restoration, and a healthy heartbeat with nonadvancing drawing frames. Existing socket/subprocess lifecycle checks exercise complete, rejected, and interrupted protocol paths; transport tests check lease/selection handling. None simulates a physical HUD. The newly consolidated SSH session orchestration has not yet run on the vehicle; it composes the previously used commands and bounded trial runner.
