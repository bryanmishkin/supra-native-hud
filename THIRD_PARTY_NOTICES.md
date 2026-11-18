# Third-party source

## PiP research credit

Credit to **[ryseek](https://github.com/ryseek)** for the G30 cluster PiP implementation and investigation of the native Screen/APIX pixel path, picture metadata, and DisplaySink handling. The reference reviewed is [PR #232](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/pull/232), branch `g30-cluster-map`, pinned at [`a0242e1c30d17b138845c18d6bf86ae0cd99ead6`](https://github.com/ryseek/Supra-iDrive6-Android-Auto/tree/a0242e1c30d17b138845c18d6bf86ae0cd99ead6), with discussion in [issue #226](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/issues/226).

Credit also to **Sq00ky / nanaisu and the Supra-iDrive6-Android-Auto contributors** for the upstream project. The G30 branch is a research reference, not proof of a larger Supra windshield surface. Its native video profile explicitly pauses for the HUD destination; its default J29 profile does not enable PiP video. No G30 implementation code has been incorporated by this research update. If code is reused later, preserve the source attribution, PolyForm Noncommercial 1.0.0 license, and required notices with the reused code and distributed packages.

## Existing vendored source

`vendor/nbt` is a scoped extract from Sq00ky/Supra-iDrive6-Android-Auto, commit `87fd9624f33f7ec02d812ebec02a416a3875a320`.

Required Notice: Copyright (c) 2026 nanaisu - NBT-AAD (https://github.com/Sq00ky/Supra-iDrive6-Android-Auto)

Its PolyForm Noncommercial License 1.0.0 is included at `vendor/nbt/LICENSE.md`. Keep the license and required notices with copies. Local adapter changes are described in [historical compatibility notes](docs/history/COMPATIBILITY-RESEARCH.md). The installed persistent path and current target limits are described in [COMPATIBILITY.md](COMPATIBILITY.md). Original project files are supplied for this private personal project; this repository does not add a public license grant for them.

The QNX SDK, vehicle runtime libraries, archived installers, license utilities and license material are not part of this repository. The reference HUD project was inspected separately; its unavailable HUD-specific drawing source has not been represented as our source.
