# MOST/DSI and factory HUD canvas session — 19 November 2026

Parked outdoors, engine running. V1 unchanged and running at exit. No custom graphics, coding, new installation, or diagnostic target requests were sent. Temporary SSH access was explicitly approved. All captures are private; only derived findings belong in GitHub.

## Captured evidence

| Recording | Packets | Drops | Process/RAM cleanup |
| --- | ---: | ---: | --- |
| Navigation start, visible, stop | 13,234 | 0 | verified |
| Radio selector open/close | 19,269 | 0 | verified |
| Door graphic open/close | 20,981 | 0 | verified |
| Phone box repeated appearance/close, no call | 18,926 | 0 | verified |
| Voice control appearance/cancel, no command | 17,945 | 0 | verified |

90,355 packets total. Each recorder ran for 120 seconds, reported zero interface drops and transmitted no packets. Owner confirmed every graphic in the windshield and normal V1 return after dismissal. Snapshot timestamps are host-side intervals; owner replies bound observations, not exact physical action times. The QNX epoch-format limitation remains: retain native UTC date samples rather than interpreting literal `%s` as an epoch.

## MOST observation

Observer hash `a74f2d2d0ac06e2791174879e7b88d9e38d724268b935c8f965df93ac402e9c7`; 15,069 ms, link up, one 112-entry registry snapshot, 2,609 received messages, 117 aggregated header records, no bad messages or dropped headers/snapshots, zero HUD commands. No 82/00 registry entry or FBlock 82 header was observed. This is a temporary DSI client's registry/header view, not a full bus sniffer and not proof no HUD route exists.

The first cleanup command removed the executable but failed because this QNX image lacks `rmdir`. The native process was absent. A separately logged exact-directory `rm -r` removed the remaining RAM directory and verified absence (exit 0). Preserve the original incomplete result alongside `cleanup-followup.json`; do not rewrite it into an initial success. The runner now uses the established QNX-compatible removal command. Server-side registration release is still not independently demonstrated.

## Concrete routing findings

Navigation start produced two DisplaySink selection events: scale 1, 460×237, selection 1, with matching completion packets. Factory endpoint HU port 65499 ↔ cluster port 30503. The known decoder found two detailed guidance models (07000000/07000001), each with high-guidance image reference FFFFFFFF. Subscription renewals, ACK packets and two TTL-zero unsubscribe packets were captured. This establishes the observed factory sequence, not a custom windshield pixel binding.

Radio, phone and voice windows contain B00E list/control method activity and V1 B006 traffic, with no decoded B009 renewal/selection events in those windows. Different factory HUD graphics must not all be equated with native PiP image transport.

Door window additionally contains 12 B011 packets: four method-1 requests, four replies, four 8002 notifications. B011 was absent from the radio recording. This is an association and an offline tracing lead; do not yet label its payload a door bitmap or claim it exclusively caused the graphic. Exact packets and times are saved privately.

## Speed and speed-limit evidence

Pinned reference `car/vehicle.hpp` names Vehicle 05/00 function 0621 as CarSpeed2, with a reference scale of 1/64 km/h. Neither 0621 nor DrivingCondition2 0626 appeared in this parked observer window. Other Vehicle functions, including RPM 0cd0, did appear. No speed payloads were captured by the header-only observer, no changing MPH trial was performed, and the reference scale is not a newly verified Supra result.

Saved HmiMain3D firmware contains named proxies `CPxyVehicle::CCarSpeed2`, `CPxyKombiInterface::CUnitSpeedSpeedometer`, and `CPxyCANDevicesDriverAssistance::{CActualSpeedLimitRecognition,CNextSpeedLimitRecognition}`. NavNBTEvoController contains corresponding speed/limit processing names. These are concrete mapping leads, not established on-wire IDs/payload schemas or windshield pixel sources. Do not conflate a user-set speed warning, recognized roadside limit, map limit and vehicle speed.

The owner offered a drive. It was not undertaken for this test because the current MOST observer records headers rather than speed values. Prepare a justified value recorder before requesting movement. Existing Ethernet recordings contain the normal stationary HUD context, not verified speedometer-rendering traffic.

## Preservation and remaining work

All 15 installed file comparisons matched before/after. Permanent fault records were unchanged. Owner confirmed normal V1 after each transition. All five native recorders and the MOST observer exited and their unique RAM paths were removed. No factory checkbox changes requested during this session; Navigation remained checked.

Enough evidence is retained to analyze the requested factory transitions offline. Not established: a larger custom canvas, complete reverse engineering of the receiver, bus-wide MOST coverage, live MPH calibration or decoded speed-limit payloads. Next offline steps: trace B011, compare B00E model payloads across radio/phone/voice, trace the named speed proxies and correlate navigation subscription/selection with image references. Do not repeat these captures merely because a narrow decoder returns no image event.
