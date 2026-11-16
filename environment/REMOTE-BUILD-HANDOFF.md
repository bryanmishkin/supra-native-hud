# Building on another authorized host

This source can be built on an existing full ARM-capable QNX SDP 6.5 Linux installation using GCC 4.4.2 and `build-observer.sh`. The local Mac build now works; remote building is an alternative, not a current requirement.

Supply QNX_HOST and QNX_TARGET for that installation and its normal license configuration. Do not copy an SDK or license into this repository. The script produces three ARM candidates and supporting objects. Run the host test suite separately; compilation does not execute the ARM candidates.

Return the compiler version, complete build output and SHA-256 hashes with the candidates. Audit the ELF interpreter, architecture, DT_NEEDED dependencies, strong imports and symbol versions against the private runtime captures before creating a car kit. No OEM runtime binary is needed to compile the current source, and none should be sent with this handoff.

The source-only bundle contains the required vendored library headers/client code and their license notices. Preserve those notices. No third party has been contacted or sent this project by this workflow.
