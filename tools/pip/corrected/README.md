# Corrected, separately bounded PiP producer

This is a separate experimental producer, not an installed V1 component. It uses the captured 277×160 HUD-style geometry and native metadata codec for explicit guidance type 8402, Day or Night. It does not claim a physical windshield connection.

Before any Screen context creation, the producer requires an owned B009 subscription ACK plus the measured selection-1 event and completes that handshake. Selection 1 is cluster negotiation, not a windshield grant. The transport lifetime is explicitly 45 seconds; existing callers retain their own shorter requested bounds. Forty-six seconds is rejected.

The producer checks V1 STOPPED/socket absence and requires OTHER2's measured 800×480 output to have no windows or scene. Its private window uses the previously examined decimal ID268444457 (masked nonfactory surface9001); it does not use factory1056. LayerManager's unmatched high-bit route preserves the producer's explicit second-display selection. This is local placement evidence, not proof that the pixels reach the windshield. The orchestrator must independently confirm no prior test producer or matching window remains.

Build offline using captured libscreen:

```sh
sh tools/pip/corrected/build.sh /private/captured/libscreen.so.1 /private/new-build
```

The output is `supra-pip-corrected-marker-qnx`. The build uses the existing QNX container with networking disabled and read-only source/library mounts. It does not rebuild V1.

Target invocation, only through the reviewed parent test orchestrator:

```text
supra-pip-corrected-marker-qnx --parked-experiment 251658244 day|night /tmp/supra-pip-corrected-<16-to-32-lowercase-hex-run-id> <producer-ipv4> <receiver-ipv4> <sink-port> <sd-port>
```

There are no default addresses. The run directory must already exist, be owned by the executing user, and grant no group/other access. Both `go` and `stop` must be absent at admission. The orchestrator creates an empty regular `go` file in this private directory only after the guidance graph is acknowledged. The producer waits at most ten seconds for that file while renewing its lease, then prints `VISIBLE_WINDOW_STARTED` and posts for a full thirty seconds. Setup and visible display together remain below the forty-five-second deadline. A late go, lease loss, changed V1 state, signal or stop file ends the attempt and reports an incomplete visible window.

Output includes exact schema-3 `PIP_BINDING`, separate owned-window identity, `SINK_NEGOTIATED_CLUSTER`, `PRODUCER_READY`, `VISIBLE_WINDOW_STARTED`, and final cleanup/full-window fields. Read-only first-post and pre-removal display snapshots preserve actual pipeline evidence. Cleanup destroys only this window/context and sends subscription TTL0. The parent separately withdraws guidance, disposes its resource, verifies absence and restores V1. Successful local cleanup is not remote image-removal proof.

Screen ABI and ownership implementation is adapted from the credited ryseek reference in `vendor/ryseek-pip`; the corrected image metadata comes from captured native serializer/renderers. See that vendor directory for licensing and provenance.

A blocked native IPC call is not proven interruptible by these offline checks. Missing final cleanup output remains an unknown cleanup state; the host must not infer resource release from an expired timer or a terminated SSH process.
