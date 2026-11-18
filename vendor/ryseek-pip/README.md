# Scoped native Screen producer

Credit: **ryseek**, with **Sq00ky / nanaisu and the Supra Android Auto contributors**.

Source: [PR #232](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/pull/232),
commit `a0242e1c30d17b138845c18d6bf86ae0cd99ead6`, files under
`milestone-7/src/cluster/video/native/`:

- `native_screen.hpp`
- `native_metadata.hpp`

Required Notice: Copyright (c) 2026 nanaisu - NBT-AAD (https://github.com/Sq00ky/Supra-iDrive6-Android-Auto)

These files retain the [PolyForm Noncommercial 1.0.0 license](LICENSE.md).
No Android Auto decoder, foreign captured navigation graph, service supervisor,
network alias setup, or installer is included. The local experimental profile
is supplied separately under `tools/pip/include/`. It is not a verified Supra
windshield profile. Local edits, if any, are recorded below.

Local change: none at initial import. The separate wrapper bounds the producer
to thirty seconds and supplies an asymmetric static marker, not live RPM.
