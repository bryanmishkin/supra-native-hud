# Build and test environments

Run commands from the repository root unless specified. Building is offline preparation; it never installs the app. The accepted target is QNX 6.5 ARM little-endian on NBTevo_T24081I. See [compatibility](../COMPATIBILITY.md) before building for another target.

## Host tests without QNX

```sh
docker build --platform linux/amd64 -t supra-hud-build-host:22.04 environment
docker run --rm --platform linux/amd64 --network none \
  --mount "type=bind,src=$PWD,dst=/workspace,readonly" \
  supra-hud-build-host:22.04 sh environment/test-host.sh
```

The Ubuntu 22.04 image contains 32/64-bit compilers and Python, not a QNX SDK. `test-host.sh` runs core/bitmap/DSI prototype tests and Python discovery. It does **not** run the separately invoked native resident/worker integration suites below. Python tests can also run directly with `python3 -m unittest discover -s tests -p 'test_*.py' -v`; some native fixture tests depend on available compilers and platform tools, so inspect skips as well as passes.

## Persistent runtime integration

On a host with a C++98 compiler, Python 3 and libpcap development headers/library, supply a previously prepared private `SHP1` profile. Both scripts use loopback peers, not the car. Output directories must be new.

```sh
sh environment/test-standalone-offline.sh /private/supra-profile.bin /tmp/supra-worker-review
sh environment/test-resident-offline.sh /private/supra-profile.bin /tmp/supra-resident-review
```

These exercise the real worker/supervisor code under `SUPRA_TEST`, including handoff, return, cleanup failures, input recovery and races. They do not establish a different vehicle's wire/profile compatibility. The base Dockerfile does not install libpcap development headers; do not assume it can run these two native suites unchanged.

Both hook ABIs can be tested in the Linux host image:

```sh
docker run --rm --platform linux/amd64 --network none \
  --mount "type=bind,src=$PWD,dst=/source,readonly" \
  supra-hud-build-host:22.04 sh /source/environment/test-handoff-abis.sh
```

## QNX ARM build

Supply a separately installed full ARM-capable QNX SDP 6.5 Linux SDK, including `host/linux/x86/usr/bin/qcc` and ARM target libraries. The build explicitly selects `4.4.2,gcc_ntoarmv7le_gpp`. An x86-target-only SDK is insufficient.

```sh
QNX_SDK_DIR=/path/to/qnx650 QNX_LICENSE_DIR=/path/to/qnx-config \
  sh environment/run-build.sh
```

Build the ordinary host image first. The helper mounts SDK/configuration/source read-only, copies source to a container-owned directory, builds with networking disabled and copies outputs into `build/`. It does not activate an SDK or support a network license server in this mode. SDK access/configuration must already work.

On the original prepared Mac only, the privately retained image can instead be used:

```sh
sh environment/run-local-sdk-build.sh
```

Its default name is `supra-qnx650-build:local`, overridable with `QNX_BUILD_IMAGE`. This is not a downloadable repository dependency or a promise that another machine has the SDK. Neither the SDK/image nor license material belongs in GitHub or a source distribution. The private evidence retains provenance; successful compilation alone is not a license-entitlement conclusion.

The build invokes `build-observer.sh`, whose historical name predates the persistent app. It now builds the resident, worker, two gates, handoff library, two startup transactions and state utility as well as research tools. The persistent kit's exact component list is `BINS` in `tools/prepare_persistent.py`.

Some build messages still describe the individual historical prototype targets or say no deployment was performed. They do not mean the current app is uninstalled. A fresh build is nevertheless a new binary set until its hashes are matched to tested evidence.

## Audit and package

Static executable audits require `pyelftools` and the target's separately captured runtime libraries in a flat directory:

```sh
python3 tools/audit_target.py build/supra-resident-qnx \
  --runtime /private/vehicle/runtime --output /private/vehicle/resident-audit.json
python3 tools/audit_target.py build/supra-standalone-parked-qnx \
  --runtime /private/vehicle/runtime --output /private/vehicle/worker-audit.json
```

Audit all target executables and review dependency closure, imported symbols, interpreter and ABI against the intended target. `audit_target.py` expects an executable interpreter; it is not a shared-library approval tool. Review the hook's exports/imports and both factory ABIs separately, then exercise the isolated hook/loader checks before actual factory integration. Static inspection does not execute or certify a candidate.

Record source revision and SHA-256 for every binary; package only that reviewed set with [prepare_persistent.py and the installation runbook](../PERSISTENT-INSTALL.md). The installer verifies kit hashes/readback, but preparation itself does not run audits. Never publish the generated private kit as a generic release.
