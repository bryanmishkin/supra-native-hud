# Next session: combined bitmap and canvas tests

Owner requested these cases in the next trip on 19 November 2026. Keep installed V1 intact; temporary tests only, parked outdoors. Allow about 45 minutes, including recovery and V1 verification; this is an estimate, not a deadline guarantee. Announce WATCH NOW only after posting succeeds. Canvas windows are30seconds; rate confirmations are120seconds.

## Before drawing

1. Confirm V1 updating, route guidance stopped, radio/phone/voice overlays closed, HUD Navigation checked. Verify V1 baseline hashes and recovery method.
2. Obtain this boot's B00E profile, idle focus, and full factory Carousel model0x6d snapshot. Save exact source capture. Do not use an old research snapshot or invent admission flags. If a brief ordinary menu action is needed, begin recording first, capture the actual Carousel update, then return to idle. A radio/voice model is not a substitute.
3. Pause V1 cleanly using V2-CAR-TEST.md; verify test bitmap absence. Record admission from current evidence. If the current Carousel restoration snapshot is unavailable, B00E cases stay blocked; tell the owner immediately, before repeated drawing attempts.

## Ordered cases

| Order | Path / item | Image | Bitmap size | Proceed only if |
|---|---|---|---|---|
| 1 | Known B006 road-icon path | White border/cross | 150×36 | V1 paused; existing runner admission passes |
| 2 | Same B006 path | IU trident | 150×36 | Case1 visible and cleanly removed |
| 3 | B00E Carousel icon field | White border/cross | 36×36 | Current-session snapshot/admission and pool checks pass |
| 4 | Same B00E item | IU trident | 36×36 | Case3 custom pixels visible and cleanup passes |
| 5 | Same B00E item, maximum advertised bitmap | White border/cross | 128×128 | Case4 visible and cleanup passes |
| 6 | Same B00E item | IU trident | 128×128 | Case5 visible without concerning clipping and cleanup passes |

Between cases2and3, run the [Hz validation sweep](HUD-HZ-VALIDATION.md) on the known B006 path. This is a separate measurement block:30-second numbered-frame steps, then120-second confirmations near the measured boundary. High-frame-rate video is required to verify visible Hz; absent usable video, do not claim a visible maximum.

These compare two established protocol paths/item types; they do not assert two independently usable windshield canvases. Size means bitmap dimensions. Actual windshield extent, scaling and clipping are measurements from this session.

For each case record: exact source pixel hash; request/response journal; posting time; windshield/cluster/both/neither; full border visible or clipped; apparent size compared with V1; image absence after removal; restore/dispose ACKs and final presence=false. Ask the owner to distinguish custom trident/cross from factory arrows. Save a stationary photo/video if the owner supplies one; it is optional.

Do not automatically chain cases. Obtain visual removal confirmation before the next. If the small B00E custom image is absent, an arrow appears instead, or upload/binding is rejected, save the exact result and stop the dependent size ladder. Do not repeat the same failure at larger sizes. Uncertain cleanup takes priority over further tests.

## Commands and assets

- Generate fixtures: `python3 tools/prepare_bitmap_test_set.py NEW_DIRECTORY`.
- Cases1/2 use `tools/run_shared_roadicon_trial.py` with existing verified session arguments, `--guidance-stopped --graph-variant empty-direction-zero --window-seconds 30 --bitmap-bgra` pointing to the matching150×36 file. Do not feed a square fixture to this runner.
- Cases3–6 use `tools/b00e_bitmap_trial.py`; exact current-admission contract is in B00E-EXECUTABLE-TEST.md. Refresh admission before each case. Pass `--size 36` or `--size 128` and the matching BGRA fixture. Existing verified loopback SSH forward required. No persistent installation or new factory instance.
- Prepared fixtures are in the private `b00e-binding-deep-2026-11-19/markers` output directory and accompanying Drive archive. Public source regenerates them identically.

Phone, voice, entertainment-list bitmap substitution and PiP expansion are **not** additional drawing cases in this trip: no complete executable binding/restoration contract exists for them. Existing captures remain available for offline work. Do not turn this session into open-ended discovery.

## Exit condition

Withdraw the final test, restore the exact factory Carousel snapshot, remove only the tracked bitmap, and verify absence. Restore V1 with the established restart procedure, verify unchanged baseline files and smooth live RPM, and obtain visual confirmation that both displays are normal. Preserve all journals and owner observations, then tell the owner they can unplug. Push derived findings/source to GitHub and archive private evidence to Drive.

## Canvas-agent final review

The canvas agent reviewed this combined plan on19November2026 and confirmed all six supported executable cases are included.64×64 and96×96 are not prerequisites. If36×36 passes but128×128 fails or clips, record those tested bounds; do not claim an exact size limit. Phone, voice and PiP drawing remain excluded. Current-session admission is still mandatory before B00E execution. The Hz probe measures its stated test path; a verified hardware-wide maximum must not be inferred from a host-limited rate.
