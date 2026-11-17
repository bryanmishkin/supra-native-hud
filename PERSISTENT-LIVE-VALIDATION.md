# Persistent installation validation — 17 November 2026

Persistent v1 installation committed — 17 November 2026

Revision08 passed automatic startup, factory navigation handoff with verified cleanup and automatic return, and radio handoff with verified cleanup and automatic return twice. The uninterrupted acceptance run reached 1,238 frames, live RPM 656.5, worker_starts=7, clean_stops=3, available=true and quarantined=false. User confirmed smooth live RPM without symbols or flashing.

The installer commit succeeded at approximately 08:55 America/Chicago. Persistent enabled token, both loaded hooks, healthy worker and read-only filesystem were verified before the final restart. After that restart the user confirmed: "Restarted; tachometer visible and smooth." The user then unplugged ENET, performed another independent iDrive restart, and confirmed: “Yeah it worked on my reset.” This verifies automatic startup without the Mac connected. Installation was left enabled.

Post-commit restart was visually verified by the user; a new machine-readable runtime snapshot after that restart was not obtained before disconnect. Full vehicle cold sleep/wake and road endurance remain untested. Earlier failed candidates and their evidence are retained. Final code revision before documentation update: fd55e97. Private kit SHA-256: 84e5233be33e68bf305028cdb232d6e49f2f939af702ab69d44134768859078a.


## Firmware-specific corrections made during validation

- HMI inherits `libEGL_X.gpp.so:libGLESv2_X_FORWARD.gpp.so:libKD_X.gpp.so`. Preserve that exact factory graphics preload and prepend the handoff hook. Unknown inherited preloads fall back to original startup. The resident child does not inherit the graphics preload.
- Warm restart can leave an exact server keepalive on an older TCP connection, or a SYN/old-ACK/reset exchange with no drawing data. Neither grants admission or represents a shared drawing change. Connections with tracked shared messages or partial data remain guarded.
- `getBytesWritten` provides the actual pre-send packet size, but the adapter fills the SOME/IP header length later. Normalize that field only in a private comparison copy. Never modify the factory buffer. A bounded no-drawing inspector captured 132 navigation/radio pre-send messages; replay with synthetic correlated acknowledgements reached both explicit idle states.
- Wait at least 30 seconds from resident startup before allowing a worker, in addition to the normal explicit factory-idle requirements. RPM transport has a 200 ms deadline; the original 300 ms freshness limit remains. Transport errors log the cause, errno and elapsed time.
- A verified-clean RPM transport failure allows up to three retries with 1/2/4-second backoff. Thirty seconds of stable worker lifetime resets the consecutive retry budget. Uncertain drawing cleanup, malformed input, lost capture or exhausted retries disables the app.
- A worker that has acknowledged CLEAN may close its socket while exiting; this is not a startup failure. A factory request arriving before worker admission revokes that permission before any drawing, without requiring a not-yet-created worker control socket.

## Target evidence

Original startup files and factory executables matched the private kit. The exact HMI SomeIP dependency exports passed inspection. Both startup wrappers passed an unarmed normal restart with original factory programs and no hooks. All configuration writes were read back and `/fs/sda0` returned read-only.

Earlier candidates stopped before drawing or removed their resources before stopping. One candidate ran 22 frames before an RPM timeout; another completed a 168-frame run and clean navigation handoff before a supervisor exit-race false alarm. An independent resource-presence check found all ten bitmap IDs absent after the earlier clean stop. These failures are retained as evidence, not counted as acceptance passes.

On revision08, the user confirmed automatic tachometer visibility. Navigation handoff stopped a 131-frame worker with `cleanup_verified=true`; factory navigation was normal in both displays and the tachometer returned automatically after guidance stopped. Radio handoff stopped the next 61-frame worker with verified cleanup. The user confirmed normal radio display and automatic tachometer return twice. The supervisor remained healthy through those transitions.

The final acceptance status and persistent-install result are recorded in the private session report. Full cold sleep/wake and road-use endurance are separate from these parked checks.

## Regression evidence

Native host supervisor/worker integration covers navigation and radio return, delayed clean process exit, pre-admission takeover, input recovery and retry exhaustion. Uncertain drawing acknowledgement still quarantines without automatic retry. Factory-gate fixtures check exact graphics preload preservation and unknown-preload fallback. Captured boot replays do not grant drawing permission. QNX ARM builds and captured-runtime import audits pass for the revised components.
