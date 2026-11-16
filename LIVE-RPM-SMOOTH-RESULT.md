# Smooth live RPM drawing verified — 16 November 2026

Two parked 30-second measured-RPM trials were completed. The first repeatedly detached and replaced the visible image; Bryan corrected the initial observation to say it was flashing. The second uploaded into an alternate bitmap slot, switched both custom references, and then removed the former image. Bryan confirmed: “Updates smoothly; flashing gone.”

| Run | Valid readings | Observed RPM range | Maximum RPM response latency | Uploads / requests |
|---|---:|---:|---:|---:|
| Remove then replace, flashing | 114/114 | 626–4455 | 27 ms | 114 / 1049 |
| Two-slot update, smooth | 120/120 | 632–6132.5 | 35 ms | 120 / 865 |

The observed ranges are measured OBD data, not an instruction to rev and not an independent calibration against the factory gauge across that range. Both tests were requested while parked; no driving validation occurred. The second sample span was 29.928 seconds and updates averaged about4Hz. The circle remains a separate unresolved navigation artifact.

## Implementation

The opt-in `--double-buffer` live test uses only the two highest bitmap slots in the previously verified allocation. Preflight still requires the whole bitmap pool empty. Every new slot is checked absent, tracked before upload, uploaded, and checked present. The high-detail and road-icon references switch to the new slot before the old slot is disposed and checked absent. The reference switches are acknowledged sequentially, not guaranteed hardware-atomic. Their visible result was smooth in this run.

Live reads use the proven DME010C path and render with the native C++98 bitmap generator. Request-start timestamps and a300ms freshness check guard each bind. Sampling is limited to approximately4Hz, with100ms individual RPC/read/renderer deadlines and a10- or30-second test duration. This is experimental operator-supervised drawing with guidance stopped, not exclusive ownership or automatic factory-navigation arbitration. Thresholds remain illustrative; the native demo renderer supplies explicit experimental permissions, not evidence of a production ownership contract.

Upload errors now defer disposal until graph withdrawal is attempted, so failure while preparing the second slot does not automatically dispose the still-visible first slot. In a simulated invalid-RPM case, cleanup succeeded. In a simulated lost-upload-acknowledgement case, the transport was marked failed and cleanup was explicitly uncertain; no blind reconnect/retry occurred. Software timeouts cannot guarantee remote erasure after a transport failure. A production system still needs a reliable remote expiry/ownership contract.

## Verification and cleanup

The offline two-slot simulator checks every disposal against both active references and confirms successful cleanup on normal completion and invalid-RPM cancellation. It also verifies transport failure is reported rather than labeled clean. The normal simulated30-second loop completed122 uploads; simulation timing differs from the car. All212 Python tests pass, including explicit second-slot authorization bounds.

Both live trials completed all seven graph-cleanup acknowledgements, final tracked-bitmap disposal and negative presence checks. Intermediate old-slot disposals/checks were acknowledged throughout. The factory instance was not disposed. Both forwards were canceled. Bryan confirmed the tachometer and circle were gone from both displays after the smooth run, and then confirmed factory navigation, radio, iDrive and HUD all normal. Local SSH master was closed; vehicle SSH was not explicitly disabled.

Private evidence: `live-rpm-drawing-2026-11-16`, including both live packet sets, raw measured RPM/timestamps, result journals, corrected visual observations, offline normal/fault simulations and summary. Original flashing run is retained. This proves the bounded live-update path and its observed flicker fix; it does not establish driving readiness, automatic navigation coexistence or circle removal.
