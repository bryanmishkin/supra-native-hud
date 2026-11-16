# Build environments

## Ordinary host tests

`Dockerfile` prepares Ubuntu 22.04 amd64 with 32/64-bit C++ compilers. It contains no QNX SDK. Run `test-host.sh` with the source mounted read-only at `/workspace`; test outputs stay in the disposable container. Python session/capture preparation tests require only the standard library. Static ELF audits additionally require `pyelftools`.

## Working local QNX build

The prepared Mac retains `supra-qnx650-build:local`, containing the installed QNX 6.5 ARMv7 GCC 4.4.2 environment. Run `sh environment/run-local-sdk-build.sh` from any directory. The helper mounts this source read-only, copies it to a container-owned directory, builds offline, retrieves candidates to `build/`, and removes that build container. Keeping build writes inside the container avoids cross-host file-ownership failures.

This local image is not in GitHub or the Drive source bundle and must not be published as a source artifact. The private project evidence records the archived SDK provenance and the user-directed generated-key installation. Successful compilation is a technical observation, not a license-entitlement or long-term activation conclusion. A vendor-issued SDK/license replacement can use the import path below.

## Import a separately installed SDK

Set `QNX_SDK_DIR` to a full ARM-capable Linux SDP 6.5 installation containing `host/linux/x86/usr/bin/qcc` and `target/qnx6/armle-v7`. Set optional `QNX_LICENSE_DIR` to its vendor-activated configuration directory. `run-build.sh` mounts these read-only, sets QNX_CONFIGURATION when provided and builds with networking disabled. It does not activate a license or support a network license server in this mode. Public x86-target-only packages cannot produce this ARM application.

The scripts select `4.4.2,gcc_ntoarmv7le_gpp` explicitly. Generic `qcc -V` enumeration in the inspected image reported no targets, while this explicit variant compiled successfully. Ubuntu 22.04 is an empirically working host for these builds, not a claim of QNX's historical supported-host certification.

The SDK compiler does not execute the output on the vehicle. Save a target ELF audit and a SHA-256 for each candidate before preparing a car kit.
