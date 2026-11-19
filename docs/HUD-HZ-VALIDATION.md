# Verified visible update-rate test

Owner requested a verified maximum, not a guessed Hz rating. Added19November2026. V1 installed files remain unchanged. Use known B006150×36 path first; do not conflate its results with B00E128×128.

## Executable probe

`tools/run_shared_roadicon_trial.py` now has `--synthetic-hz` and `--hz-seconds`. Run with the existing current verified session inputs, `--execute --guidance-stopped --double-buffer --graph-variant empty-direction-zero --synthetic-hz RATE --hz-seconds 30`. Do not combine with live RPM or static bitmap input. No revving or driving is needed.

Every frame has a unique six-digit number and a16-bit Gray-code strip. It uses the prior double-buffered road-icon update/cleanup path. Synthetic data isolates drawing throughput from the factory RPM feed's separate sampling interval. Rate testing does not change the persistent worker or claim its native-loop maximum.

Start at1,2,5,10,15,20,30,40,60Hz, in order,30seconds per run. Stop escalation on a full-frame transaction exceeding the requested period, timeout, protocol rejection, flicker, unexpected graphic or incomplete cleanup. No catch-up burst is allowed. Restore/absence and visual checks separate every run. Lower rates can be omitted only if already verified on the exact probe/build in this session.

Logs distinguish scheduled time, start time, model-post acknowledgment and completion of old-image removal. Protocol journals retain every request/reply. `hz-timing.json` identifies the requested rate and measurement scope; `hz-frames.jsonl` records each full frame transaction. Files explicitly leave visible verification false.

## What establishes the maximum

1. Record high-frame-rate video showing the numbered HUD frame, with known actual video timing.240fps is preferred for rates through60Hz. Preserve original video and metadata; converted playback speed is not capture frame rate. Camera exposure, rolling shutter, duplication and dropped camera frames must be checked.
2. Decode visible sequence changes and durations. Compare against issued sequence IDs: missing/reordered numbers, held frames, visible cadence and flicker. A smooth-looking animation alone is not a pass.
3. Establish both a passing rate and a higher failing rate. Repeat the last passing and first failing cases to separate a repeatable boundary from a transient delay. Run the selected passing rate for120seconds twice (`--hz-seconds 120`), with successful cleanup and no permanent fault additions.
4. Report requested Hz, protocol-completed Hz, visible distinct-frame Hz, duration, drop/hold counts, video timing uncertainty, resolution, transport, build and cleanup. Label the result **highest verified sustained visible rate under these conditions**, with the tested failing upper bound.

If60Hz passes, report “at least60Hz verified,” not “60Hz maximum.” If video cannot resolve the next rate, report a measurement ceiling. If the host/SSH/network/serialized request loop misses deadlines before visible refresh saturates, report a **harness-limited** result; this does not establish the receiver or native production app maximum. Do not increase limits blindly or fabricate a maximum to close the task.

## Delay measurement

Request-to-ACK timing is not pixel-display latency. Video measures visible inter-frame cadence. Absolute input-to-visible delay additionally requires a recorded synchronized source reference; without it, report only the measured protocol delay and visible cadence separately. Factory RPM input-to-HUD delay is a separate test from these synthetic drawing frames.

## Session order and recovery

Perform after the150×36 control/trident cases and before the B00E experiments, while V1 is cleanly paused. Budget roughly10–15additional minutes for sweeping, repeats, confirmation and cleanup, potentially longer if a failure needs recovery. Keep the car parked, overlays closed, and known iDrive recovery available. Do not leave the test running for a drive. Use existing recovery if the computer/connection fails; the duration is not a receiver TTL. Restore verified V1 at session end.
