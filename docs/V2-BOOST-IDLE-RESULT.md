# V2 pressure/display session — 18 November 2026

**Pressure acquisition, combined V2 display, cleanup and V1 restoration passed in a parked session.** Two complete pressure-only windows also passed after the owner confirmed ENET fully unplugged. This establishes continuation without the cable during this boot, not cable-free cold-start availability or pressure calibration.

Candidate worker: `d4221ed7ed3faa87dca55799545b9028f91de96351e9b6638d0951623912b565`. The exact compiled candidate was staged in RAM. No persistent V1 binary, profile, startup configuration or enable/disable token changed.

## Connected measurements

- Initial pressure-only probe: 40/40 valid pairs; absolute candidate 99.242188–99.304688 kPa; ambient 99.359375–99.367188 kPa; derived gauge value approximately −0.018 to −0.008 PSI. Maximum individual reply latency: 26 ms. Zero HUD writes.
- Brief five-second layout-only gate passed with verified cleanup.
- Thirty-second combined run: 120 pressure pairs, no failed pairs, 120 boost-visible frames, successful timed completion and cleanup. Maximum logged RPM sample gap: 327 ms.
- Owner reported: “RPM smooth; PSI readable near zero.” Both displays were confirmed normal afterward.

Although planned as an idle test, the recorded combined-run RPM range was 635–5803 and derived PSI ranged −0.434547 to +3.027096. Keep the actual recorded range rather than label the entire run steady idle. These observations have no independent pressure reference and do not validate positive-boost calibration or identify the sensor location.

## Cable-free measurements

A detached script on the head unit ran three bounded pressure-only probes, without drawing. Each returned 40/40 valid pairs and exit 0. The owner confirmed unplugging ENET completely from the car at 14:40:02 UTC. The first window started at 14:39:50 UTC, before that confirmation, so it is not counted as a completely confirmed cable-free window.

Windows starting at 14:40:10 and 14:40:30 UTC both occurred after unplug confirmation and before reconnection: **80/80 confirmed cable-free pairs**, maximum reply latency 26 ms, derived PSI approximately −0.018 to −0.008. The recording finished and its files were retrieved before the restart.

This shows the gateway continues serving these pressure requests with ENET absent after earlier connected access. It does not prove the gateway will be available from an untouched cable-free cold boot. It also does not constitute a combined-display cable-free test.

## Restoration and preserved evidence

The owner restarted iDrive and confirmed the original V1 returned and updated. The runner then verified original installed hashes and startup files, enabled state, read-only filesystem, both factory hooks, absence of the temporary V2 directory, a healthy supervisor, advancing heartbeat and live RPM frames/sample timestamps. Final status showed one running worker, no quarantine and available admission. All five permanent fault files were byte-identical before/after.

All session phases passed; no recovery-required flag remained. No additional navigation/radio test was performed because the installed V1 was unchanged and this session targeted pressure/display behavior. V2 was not installed persistently.

Private archive: `Supra-HUD-V2-Boost-Idle-Passed-V1-Restored-2026-11-18.zip`. Includes exact kit with V1 fallback, numbered command output, raw pressure replies/timestamps, worker journals, cable-free script/results, owner observations, pre/post V1 captures, source and checksums.

Remaining acceptance: trusted pressure comparison/semantics under appropriate load; untouched cable-free cold-start pressure availability; V2 persistent operation and endurance. Do not relabel these parked results as a calibrated boost gauge or a completed V2 release.
