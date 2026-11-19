# Exact receiver firmware acquisition — 19 November 2026

The ECU60 identity is captured. Matching receiver firmware bytes are **not yet obtained**. No further car visit is required to resolve this download/access problem. No Hz tests or V1 changes.

## Targets from the actual response

| Component | ID | Required version |
|---|---|---|
| Hardware reference | 0000476d | 002_002_000 |
| BTLD | 00005ab0 | 007_001_001 |
| FLSL | 00005ffa | 007_001_001 |
| SWFL | 00005ffb | 008_000_000 |
| SWFL | 00005ffc | 008_000_000 |
| SWFL | 00005ffd | 008_000_000 |
| SWFL | 00005ffe | 008_000_000 |
| CAFD metadata | 00002660 | 014_000_000 |

Class07 is now identified as **FLSL** from [ediabaslib's published process-class enum](https://github.com/uholeschak/ediabaslib/blob/1fa7d33076e1bb2d04eb32e217abf82bef750a29/Tools/Psdz/PsdzClientLibrary/BMW/Authoring/Vehicle/SvkProzessklasse.cs). The original raw response and original capture report remain preserved; this is a later interpretation, not a new vehicle read.

For SWFL/BTLD, seek both `.bin` and `.xml` with the exact version suffix, for example `swfl_00005ffb.bin.008_000_000` and `swfl_00005ffb.xml.008_000_000`. Preserve all matching FLSL names even if their storage convention differs. Hardware identity does not imply a separate HWEL binary. Do not substitute a different software version or the BO03 reference build.

## Searches and access results

- Exact-ID searches on the public web and GitHub did not locate matching payloads. Bare hexadecimal searches returned unrelated code/data; prefixed `swfl_00005ffb` and `swfl_00005ffa` searches returned no files. This is search coverage, not proof no public copy exists.
- Local filename searches in Downloads, Documents and mounted volumes found no candidate programming dataset. The exact matcher scanned the current work directory and found no matching packages.
- The BO03 emulator source requires a supplied local PSdZData dataset and only supports its separately identified firmware. It does not supply these receiver binaries.
- Advertised full datasets and reduced Toyota S18T packages were found, but no accessible exact-file listing verified the required modules. The checked public Drive full-package link returned404. Other checked routes required login, private contact, or passed through an offer/download gate. No contact, registration, offer completion, purchase or third-party installer execution occurred.
- About45GiB of local disk was available during the search. The broad advertised datasets exceed that; a reduced package or exact-module export is the practical acquisition target. No large download was started.

## Official subscription: confirmed scope versus unresolved contents

[Toyota's registration page](https://techinfo.snapon.com/tis/register.aspx) lists Professional Diagnostic at$80 for two days. [Subscription details](https://techinfo.snapon.com/tis/SubscriptionTypeDetails.htm) include current ECU calibration downloads and explicitly require this tier for Supra ISTA-based wiring information. [Toyota bulletin T-SB-0060-24, page3](https://static.nhtsa.gov/odi/tsbs/2024/MC-11006148-0001.pdf) identifies Toyota-ISTA under TIS → Diagnostics → Scantool.

These establish the appropriate access tier and download route. They do **not** publish an archive manifest proving the current package contains our exact `008_000_000` SWFL versions, nor guarantee readable receiver code. Do not promise that paying$80 resolves the firmware match. The owner has no existing account and requested confirmation before spending. No purchase is authorized by this document.

## Offline matching tool

```sh
python3 tools/match_receiver_firmware.py \
  --capture /private/receiver-capture/04-60-f101.json \
  --root /private/extracted-programming-data \
  --output /private/new-match-report.json
```

Reads extracted directory names and hashes exact-name candidates. Produces separate wrong-version, missing-file and unclassified matching-ID lists. It neither executes nor extracts nor flashes anything. Filename matching is explicitly not content authentication. Check the source package provenance and XML identity/segment metadata before selecting a decoder. No receiver architecture, base address, compression method or root framebuffer dimensions are inferred from BO03.

Six offline identity/matcher tests pass, including unknown-class preservation, exact versions, wrong-version separation and rejecting name-only matches as firmware verification. The actual captured response produces seven software/metadata targets. Test fixtures exercise parsing only and are never evidence of real firmware contents.

## Work unlocked by actual files

Inspect matching XML and package headers first. Establish architecture and memory segments from the files; then locate receiving B006/B00E resource handlers and B009 session/job lookup, and follow them into the common composition/output target. Recover root geometry, transforms, clipping and update/removal ownership before proposing a whole-windshield drawing test. This trace cannot be manufactured from the identity numbers alone.
