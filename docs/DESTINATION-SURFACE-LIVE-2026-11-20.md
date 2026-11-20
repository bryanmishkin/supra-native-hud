# Destination-picture and narrow-tail live results — 2026-11-20

## Visual evidence

| Test | Windshield | Gauge cluster | Removal |
| --- | --- | --- | --- |
| Destination picture | Owner saw a bordered 1, finish flag and 400ft underneath. No custom cross reported. | Same observation. | Protocol checks passed; owner confirmed both clear. |
| Narrow tail, 64×36 | Owner confirmed the full amber tile, all three white marks and green right edge beside the cyan reference. | Full tile and right edge also visible. | Protocol checks passed; owner confirmed both clear. |

The narrow-tail result establishes a complete second panel alongside the known reference through the separate-entry RoadInfo layout. It does not establish increased height, a freely resizable parent viewport, or access to the full height-adjustment outline. The destination picture test did not establish visible custom pixels through the destination model: a factory finish flag is not our cross.

## Execution and evidence

The session manager verified the 15 installed V1 files and cooperatively stopped V1 before drawing. Each case used a full 30-second static window. No Hz tests or persistent V1 modifications were performed.

Private evidence is in `outputs/destination-surface-live-2026-11-20/run2`: exact source pins, case plans, sent requests, replies, result files, owner observations, and passive packet captures. The first pause attempt failed before stopping V1 because this QNX shell lacks `printf`; the missing-file fallback now uses `echo`. The active run2 kit was freshly prepared with that corrected source pin.

The first 120-second recording contains 5,176 packets with zero drops. Its recorder executable was removed, then its empty owned temporary directory was removed separately because this QNX environment lacks `rmdir`. No unrelated files were removed.

The second 120-second recording contains 5,266 packets with zero drops; its temporary recorder and owned directory were removed. Both capture byte counts match their saved PCAP files.

**Restoration deferred by owner:** after both protocol and visual removal checks, the owner explicitly requested departure without restoring V1. V1 installed files remain unchanged, but its runtime is cooperatively paused. No final restart, running-V1 verification, or completed-restoration claim was made. Restore through the established procedure at the next authorized opportunity; do not treat this as a V1 installation failure.
