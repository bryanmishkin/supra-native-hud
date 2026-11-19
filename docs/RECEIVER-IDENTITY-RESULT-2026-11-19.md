# Receiver identity capture — 19 November 2026

The missing ECU60 software inventory is now captured. This replaces the prior lack of target identifiers; it does not mean matching firmware bytes or a full-windshield drawing interface have been obtained.

## Measured identity

The actual gateway's configured-ECU reply contains25 addresses, including60. Two separate F101 reads from60 returned the same84-byte positive response, byte-for-byte, containing eight entries:

| Class | Identifier | Version |
|---|---|---|
| HWEL | `0000476d` | `2.2.0` |
| BTLD | `00005ab0` | `7.1.1` |
| SWFL | `00005ffb` | `8.0.0` |
| Raw class07 — not assigned a name by this decoder | `00005ffa` | `7.1.1` |
| SWFL | `00005ffc` | `8.0.0` |
| SWFL | `00005ffd` | `8.0.0` |
| SWFL | `00005ffe` | `8.0.0` |
| CAFD | `00002660` | `14.0.0` |

Positive F101 response SHA-256: `4406c00b629b281dba5556e98dee448fafbf368a51e8556f99063efb03259af4`.

Address60 is the candidate cluster diagnostic address identified by the referenced BMW topology. The gateway now independently confirms its presence and the endpoint returns this exact inventory. Human-readable name/part/version identifiers F197/F187/F189/F19E/F191/F192/F194 all returned `7f2231` (request out of range), so no ECU-reported marketing/system name is claimed. No secondary internet CAFD table is promoted to an ECU-reported name.

These identifiers differ from the BO03 reference's program/config/graphics identifiers3e5b/3e5c/3e5d. Do not use BO03 firmware or its memory addresses as a match. Search/select receiver artifacts using the exact identity above. A further association between this diagnostic identity and the internal Ethernet drawing service should be grounded in target topology or matching receiver implementation, not merely a similar IP suffix.

## Network and capture completeness

ENET was active on `en8`,100baseTX full duplex. Requests were explicitly bound to that adapter and its current link-local address; Wi-Fi and network settings were unchanged. Gateway3F07 was positively returned twice, with count and body length agreeing. The source list reference was previously unverified on this Supra; this session supplies the actual response and confirms the simple count/address layout for these bytes only.

The ECU's172A IP-configuration read succeeded and is preserved privately. A single connection to its reported link-local address at HSFZ6801 was refused before an application request could be sent. Gateway-routed identity reads succeeded; no direct-port availability is assumed.

The session sent15 allowlisted ReadDataByIdentifier requests across the initial and confirmation captures. Raw HSFZ frames, negative responses, identity entries, comparison results and the unsuccessful direct connection are retained privately. No VIN/serial request, address scan, programming, coding, security access, reset, memory write or SSH was used.

## V1 and final check

No V1 files, startup state, resources, processes or drawing models were changed. No Hz or drawing tests were run. The owner confirmed iDrive remained normal with no unexpected display changes. This read-only session did not verify installed hashes over SSH or perform new V1 runtime/endurance tests; previous baseline evidence remains authoritative.

## Offline continuation

The required vehicle identity input is complete. Match the HWEL/BTLD/SWFL versions to receiver firmware or documented compatible implementation, then trace resource/job lookup into the actual main composition target. The existing B00E content-field canvas tests remain separate executable widget experiments. Whole-HUD geometry and a root-pixel binding/removal API remain unproven; no additional vehicle identity visit is requested on the present evidence.
