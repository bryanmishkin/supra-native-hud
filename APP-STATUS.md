# Verified application status

**Cold-start issue reported 17 November:** the owner saw no tachometer after a cold vehicle start. Prior warm-reset acceptance remains valid but does not establish cold-start reliability. This branch contains an offline-tested repair candidate; the actual vehicle fault is not yet confirmed and the repair is not installed. See [failure, evidence and exact repair plan](docs/V1-COLD-START.md).

Updated 17 November 2026. This file is the current status; dated research reports describe their own stage of the project.

## Accepted on the reference vehicle

Reference: 2026 Toyota GR Supra 3.0 Premium, six-speed manual; NBTevo_T24081I; QNX 6.5 ARM. Accepted implementation commit: `fd55e97` (later documentation commits do not change those binaries). Private revision08 kit manifest SHA-256: `84e5233be33e68bf305028cdb232d6e49f2f939af702ab69d44134768859078a`.

| Capability | Evidence and scope |
| --- | --- |
| Native head-unit operation | QNX ARM worker ran on the head unit, with plausible live RPM checked against the factory gauge. No Mac RPM relay is needed. |
| Sport layout and colors | Owner confirmed readable larger digits/bar, no clipping, corrected orange/red lights. Simulated 5500/6200/6500 display values exercised light progression without commanding engine speed. |
| Symbol-free, smooth updates | Owner confirmed no circle, arrow or flashing. Alternating bitmap binding is used. |
| Navigation priority and return | On revision08, a 131-frame worker stopped with `cleanup_verified=true`; navigation was normal in both displays. Tachometer returned automatically after guidance stopped. |
| Radio priority and return | Next worker stopped after 61 frames with verified cleanup. Normal selector and automatic return were confirmed twice. |
| Sustained operation | Final uninterrupted worker reached 1238 frames; healthy resident, worker_starts=7, clean_stops=3, no quarantine. Owner confirmed smooth, symbol-free live RPM. |
| Persistent startup | Commit succeeded; enabled token, mapped hooks and read-only filesystem verified before restart. Owner confirmed automatic smooth tachometer after committed restart. |
| Startup without Mac | Owner unplugged ENET, reset iDrive again and confirmed it worked. This is a visual confirmation, not a post-reset machine log. |
| Factory functions | Navigation in windshield/cluster, radio selector and iDrive were confirmed normal during acceptance. |

[Detailed installation evidence](PERSISTENT-LIVE-VALIDATION.md) separates actual observations from regression tests. The accepted app was left installed and enabled. Do not apply the older “restore factory startup at the end of every demo” instructions to a passed persistent installation.

## Known design boundaries

- The app uses **shared factory guidance instance 200**, not a separately owned session. It must yield rather than draw simultaneously with factory guidance/radio.
- The demonstrated drawing path can affect both windshield and gauge cluster. There is no proven independent windshield-only destination or larger canvas.
- 150 × 36 is the implemented/observed bitmap size. Removing the circle did not establish more display area.
- Display scale 7000 and full shift cue 6500 are hard-coded. They are not engine calibration recommendations; the code's `thresholdsValidated=true` enables rendering and is not evidence of OEM limit validation.
- The app does not include a settings UI, boost display, installer GUI, automatic firmware discovery, or generic upgrade/re-enable procedure.
- Unknown factory state prevents drawing. Loss of capture, uncorrelated shared traffic or uncertain removal can disable the app until serviced. The software cannot guarantee remote image expiry after every possible transport failure.

## Not yet established

Full vehicle shutdown/sleep/wake, repeated ignition cycles, engine-off/stop-start behavior, extended road endurance, other driver-assistance overlays, and other vehicles/firmwares remain unverified. The unplugged iDrive restart is not a full cold vehicle power cycle. The complete navigation/radio acceptance happened before persistent commit; the recorded final restart checks confirmed automatic display, not a second complete post-commit handoff sequence.

## Offline evidence

At the accepted implementation revision, 244 Python tests passed. Native integration tests cover worker/supervisor handoff and return, pre-admission takeover, delayed CLEAN exit, classified RPM recovery, retry exhaustion, and uncertain-ack quarantine. Gate tests cover exact factory preload preservation and fallback. Captured boot replay tests do not grant admission. ARM builds and static import audits passed; these complement, not replace, target execution.
