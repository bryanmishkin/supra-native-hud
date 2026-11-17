> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

> **Later same-session result:** RLE32 encoding and the shared road-icon path were implemented and tested successfully. See [RLE32-LIVE-PROOF.md](RLE32-LIVE-PROOF.md). The PNG/own-session procedure below is historical.

# Own-session live drawing experiment

**Live result: the PNG drawing candidate is incompatible with the returned configuration.**
On the car, replacing the first string with the observed `BMW.IC.Guidance`
profile while preserving our distinct app/vendor changed the create response
from error to success. It returned handle **200**, the factory value. Read-only
checks through that handle saw four factory text resources become present when
the driver enabled navigation. This is evidence of shared factory resource
visibility, not an isolated app session. Its bitmap configuration advertises
**150×36, 10 slots, RLE32 only; PNG is false**. No bitmap upload, drawing or
disposal was attempted. The driver confirmed factory behavior remained normal.

The procedure below records the original candidate, not a recommendation to
repeat it unchanged. A supported RLE32 encoder and an appropriate session or
shared-resource design are needed before another visible marker attempt.
This replaces the previous transport-injected lifecycle component with an
executable Mac runner. It attempts a new session, a real PNG-backed drawing
model, withdrawal, resource disposal/check and instance disposal in one run.
It does not claim that the cluster accepts third-party sessions or that the
candidate graph will reach the windshield. Those are the experiment's results.

## One car session

Use a parked outdoor location. Engine idling and the normal windshield HUD
visible are required on this Supra; accessory mode did not display the HUD.
Leave factory route guidance stopped initially. The operator checks the wired
adapter, existing SSH connection and pinned head-unit identity before launch.
No engine-start instruction is issued until the operator is ready to run.

From the checkout, with the current verified wired addresses and known-hosts
file (and existing authenticated SSH master if necessary):

```sh
python3 tools/run_live_drawing_test.py --execute \
  --head "$HEAD_IP" --local "$MAC_ENET_IP" \
  --known-hosts "$KNOWN_HOSTS" --socket "$SSH_MASTER" \
  --output "$NEW_RESULT_DIRECTORY"
```

Omit `--socket` if direct batch-mode authentication works. These values are
session inputs, not values to guess from a previous car trip. The operator
fills them from current link checks. The launcher verifies `QNX hu-omap` and
`armle`, opens a temporary localhost SSH forward to the previously captured
cluster endpoint `160.48.199.96:30502`, and cancels the forward afterward.
Forwarding support itself has not been verified on this car. A refusal stops
with evidence; this runner does not activate SSH or alter its configuration.

The driver observes the windshield and tells the operator:
1. Whether the distinctive white box/cross appears **in the windshield**.
   The answer window is at most 15 seconds. A cluster-only image is not a pass.
2. Whether the marker is gone after cleanup (20 seconds to answer).
3. Whether factory HUD, iDrive, radio selector and navigation still work
   normally (20 seconds). Use the radio/nav controls while parked as needed.

The operator enters `yes` or `no` for each prompt. Missing observations remain
unknown, never success. The image is withdrawn immediately after the first
answer or its deadline. Do not unplug until the saved cleanup results and
factory behavior have been checked. A complete run is typically under two
minutes; the launcher has a three-minute watchdog plus a cleanup grace period.

## What is actually sent

- One create with distinct identity `SupraHUD.MarkerTrial / SupraHUD.OwnSession /
  bryanmishkin`, protocol version tuple `3,3,1`. No retry or factory identity.
- Require a successful correlated response with a handle other than reserved
  values or captured factory handle 200. Save its complete configuration.
- Require returned allocations for type 10 high picture, type 15 description,
  type 32 maneuver list and type 33 list state; require exactly one supported
  PNG bitmap allocation with bounded dimensions. Unsupported configurations
  end the test and release the returned instance without uploading a picture.
- Select the **returned offsets directly**, not `(type << 24) | offset`.
  Precheck the resource; refuse to overwrite anything reported present.
- Upload a generated black/white PNG; require resource-presence confirmation.
- Send state 1, high-picture reference, description, one-entry maneuver list,
  initialize, then state 2 referencing the description. Other optional
  description references use the observed absent sentinel `0xffffffff`.
- Withdraw with states 5 then 0, empty list, absent picture reference and
  initialize. Independently attempt resource disposal, absence check and
  instance disposal. Each acknowledgment and error is recorded separately.

This is a **minimal candidate graph**, not a proven full factory navigation
model. Whether the omitted current-state/distance/road models are permitted,
which display the new session uses, and whether its allocations are exclusive
remain live questions. The runner does not modify the factory DisplaySink,
reuse its instance, replay captured route graphs, or install a resident app.
No successful ACK alone establishes visibility, erasure or exclusive ownership.

## Evidence and result interpretation

Each run gets a new directory. `trial/` holds exact request/response packets,
received magic cookies, the PNG preview and atomically replaced `result.json`.
The actual uploaded image is recoverable from the resource request, including
its negotiated dimensions; `marker-preview.png` is only a fixed-size preview.
The result contains raw create configuration, selected IDs, all method results,
cleanup results, and the three visual observations. `launcher.json` records
connection setup and forwarding cleanup. Keep the whole directory private.

Exit 0 requires affirmative windshield appearance, disappearance and factory
function observations **plus** all cleanup acknowledgments and resource check
false. Exit 2 means rejected, inconclusive, interrupted or failed; read the
specific stage. `own_session_accepted` means the distinct create was accepted,
not that exclusive ownership or windshield routing was proved.

Timeout/partial-frame/connection-loss marks the transport unusable; no reconnect
or blind retransmission is attempted. Cleanup is attempted but may be impossible
on a lost connection. Such a result explicitly remains unverified. SIGINT and
SIGTERM trigger cleanup; SIGKILL, power loss or cable removal cannot guarantee
remote cleanup. The instance-release acknowledgment is separate from visual
removal, and neither is inferred from a closed socket.

## Offline verification

```sh
python3 -m unittest discover -s tests
python3 tools/ric_live_trial.py --output /tmp/new-hud-preflight
python3 tools/run_live_drawing_test.py
```

193 tests passed at this change, including real localhost TCP framing,
fragmented reads, magic-cookie handling, size limits, timeout poisoning,
executable CLI and launcher with a local SSH stand-in, unsupported config,
all post-create failure positions, interruption and cleanup. No car endpoint
was contacted for these checks. The stand-in is not a cluster emulator and
its acceptance is not evidence of vehicle support.

## New static evidence

Controller SHA256:
`71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`.

- `0xa665cc` strips the high byte from an internal model ID; `0xa66a38`
  extracts its type. These internal IDs are distinct from converted wire IDs.
- `0xa617e8` checks high-roundabout type 10; `0xa35440..0xa35464` requests
  its generic configuration and initializes the high container's available IDs.
- `0xa66478`, especially `0xa664bc..0xa664d0` and `0xa66550..0xa66564`,
  fills available IDs with `offset + index`, for both communication roles.
- `0xa35194` supplies configuration offsets/counts, including state at
  `0xa35318..0xa35328` and bitmap at `0xa355e4..0xa355fc`.
- `0xa34d28` maps internal high-model IDs to stored converted IDs;
  `0xab4624..0xab4654` uses those converted IDs and the model type on send.
- Method12's one-entry list encoding re-encodes the retained 46-byte factory
  body exactly. This validates field layout, not acceptance of the new graph.

No OEM binary or capture is included in the source repository. Private traces
and regression output accompany the Drive diagnostics archive.
