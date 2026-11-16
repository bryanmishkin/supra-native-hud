Live result: the windshield stepped tachometer, complete removal and subsequent factory navigation passed on 16 November 2026. Gauge-cluster tachometer visibility was not observed during this run. See [TACHOMETER-LIVE-RESULT.md](TACHOMETER-LIVE-RESULT.md).

# Tachometer drawing test — prepared 16 November 2026

The next test displays native-rendered synthetic RPM values 1000, 3500 and 6500 through the road-icon path proven in the car. Each value has a three-second observation window and a complete withdrawal/disposal/absence-check cycle before the next value. It is a staged drawing experiment, not a real-time tachometer or an independent overlay. No engine revving is needed.

## What is implemented

`src/tach_bitmap.cpp` converts the existing HudCore Frame into an opaque 150×36 BGRA image: 24 bar segments, numeric RPM and five shift indicators. HudCore continues to own freshness, cadence, thresholds and factory-overlay suppression. The offline demo explicitly supplies simulated ownership and idle-overlay inputs; these are not evidence of real ownership. Demo scale 7000/shift 6500 is illustrative, not a vehicle limit recommendation.

`tools/run_tachometer_trial.py --prepare NEW_DIRECTORY` builds the native C++98 renderer on the host and saves three BGRA/PNG/RLE frames with hashes. `--execute` runs the proven shared road-icon lifecycle for each frame. It requires explicit stopped-guidance confirmation and verified frame hashes. Any uncertain cleanup, resource absence, tunnel cancellation or failed child stops the sequence. Ctrl-C requests child cleanup; there is no automatic restart. Visual success remains false until separately observed by the operator.

The shared runner accepts one exact-size opaque BGRA frame, retains the marker as its default, and now returns a failure exit status when cleanup is incomplete. No instance-disposal command is added.

## Factory navigation handling

Production HudCore still refuses unknown or active factory-overlay state and stale RPM. This experiment does not wire a fabricated idle signal into the production app. The live experiment is explicitly operator-supervised and uses a shared factory session, so factory guidance and the radio selector must remain stopped during it.

No automatic factory-navigation detector, exclusive resource lease, or safe concurrent handoff has been established. An empty bitmap pool is not such a detector: earlier navigation used text resources while bitmap slots remained empty. Do not use pool emptiness to declare guidance inactive. Do not automatically cancel a newly started factory route to reclaim this session.

The current test performs a **staged handoff**: finish custom cleanup, confirm all test artifacts gone, then start factory guidance and check the radio selector. Unexpected factory activity during a test means abort and inspect; it is not a reason to continue updating shared state. Independent overlay coexistence and a genuine live RPM feed remain separate integration work.

## One-session procedure and pass criteria

1. Park outdoors, remain stationary, ENET connected, engine running only to make the factory HUD visible. Establish the previously verified temporary access if needed. Stop guidance and let the radio selector close. Check normal HUD before starting.
2. Run the prepared launcher once. It shows synthetic 1000 → 3500 → 6500, with a removal gap between values. Do not rev the engine or start navigation during these windows. Observe both windshield and cluster: numbers readable, bar progression and shift indicators change. Built-in roundabout/navigation artifacts may remain during each frame because the unchanged proven graph still uses those support models.
3. Each frame must have all cleanup acknowledgements, successful bitmap disposal, a negative presence check and canceled local forward. A failure blocks the next frame. Do not repeatedly rerun a failed sequence.
4. After the runner exits, confirm all tachometer and support graphics are gone from both displays. Protocol ACKs alone do not establish this.
5. Only then start factory navigation, verify normal instructions in both displays, stop guidance, check radio selector and iDrive, and confirm normal HUD. Save the operator observations alongside each result. Do not claim automatic arbitration from this staged check.

The first test must establish readability, resource reuse across full cleanup cycles and normal factory restoration. It does not validate 10 Hz animation, same-ID bitmap replacement while bound, live RPM accuracy, native runtime deployment or windshield-only routing. Do not repeat car visits to collect generic data; this is a concrete visual candidate with retained known-good protocol controls.

## Commands

```sh
python3 tools/run_tachometer_trial.py --prepare /absolute/new/frames
python3 tools/run_tachometer_trial.py --execute --guidance-stopped \
  --frames /absolute/frames --output /absolute/new/results \
  --create-response /absolute/verified-create-response.bin \
  --support-stream /absolute/retained-factory-support-stream.bin \
  --ssh-socket /absolute/active-ssh-master --head 169.254.199.119
```

Default invocation makes no network connection. The saved private evidence package supplies the measured reply and support stream; OEM captures are intentionally not committed to GitHub.

## Offline validation

- 204 Python tests pass, including sequence termination on uncertain cleanup and frame tampering rejection.
- Native C++98 tests pass on the Mac and 32-/64-bit Linux, including renderer bounds/alpha, segment state, unknown-overlay suppression and factory-overlay yield. Existing application tests cover stale input and permission revocation during a draw.
- Full QNX ARM build passes; `supra-tach-bitmap-demo-qnx` is an ARM EABI5 executable using the QNX loader. It is an offline image generator, not a vehicle-installed app, and was not run in the car.
- All three frames round-trip through RLE32 without pixel changes; sizes are 2912, 2856 and 2872 bytes.
- Four offline protocol replays (original marker plus three tach frames), 32 requests each: the marker is byte-identical to the successful car test; every tach replay differs only in bitmap-upload method3. All graph and cleanup packets remain byte-identical. Mock replies test client behavior, not actual cluster acceptance of new pixels.
