# Native DisplaySink transport and pixel-binding boundary

19 November 2026. Offline implementation; V1 application, installed files, baseline and tags unchanged. **No new larger-windshield test is admitted.** This implements the missing network stage, but does not claim that stage alone repairs the failed image path.

## Implemented beyond the earlier codec

`tools/pip/include/displaysink_transport.hpp` is a native C++98 POSIX transport, compiled for the retained ARM QNX 6.5 toolchain. It owns a new TCP connection and an ephemeral UDP socket, advertises the actual connected TCP endpoint, subscribes to B009/event group 1 with captured TTL 3, renews at one-second intervals, checks the exact ACK source and shape, handles fragmented selection frames and cookies, and sends the captured completion only after a valid ACK. UDP and TCP arrival order may differ; a pending selection waits for its ACK. Whole lifetime is bounded to at most 30 seconds.

It accepts only the evidenced `(scale 1, width 460, height 237, selection 1)` tuple. That means **Kombi negotiation**, not windshield permission. Unknown destinations/geometries fail closed. It never forces selection 0. NACK, lease expiry, malformed frames, stream closure or lifetime expiry invalidate negotiation, send a TTL-zero unsubscribe if subscribed, and close only owned sockets. Unsubscribe sent is not proof of receiver image removal.

There are no vehicle endpoint defaults, factory port reuse, network configuration changes, shared socket options, Guidance calls, Screen writes or V1 operations. The production producer-IP ownership question remains unresolved; callers must not supply a reference-car alias by guess. The class is not wired into the retired live runner. The accompanying executable hard-codes loopback and cannot launch a car drawing test.

The source is independently implemented from captured packet shapes. ryseek's G30 PiP work identified the missing startup ordering; retain [third-party credit](../THIRD_PARTY_NOTICES.md).

## Validation

`python3 -m unittest discover -s tests -p 'test_pip*.py'`

The final suite passed 42 tests, including 10 new native socket tests. Native tests use real local TCP/UDP sockets, not mock network classes. The Python captured-wire codec independently checks advertised endpoint and completion bytes. Coverage includes fragmentation, renewal, selection-before-ACK, spoofed-source rejection, unsupported HUD selection, negative ACK, expiry, oversized frame, wrong group, no-ACK timeout and partial-frame peer closure. These are transport tests; they do not simulate the cluster or prove visible pixels.

`sh environment/build-pip-handshake-check.sh /new/private/output`

Builds an ARM QNX loopback check under an isolated no-network compiler container. It does not install or execute on the vehicle. The strict ISO C++ build initially hid QNX POSIX declarations; the final build uses GNU C++98 as required by these SDK headers. No SDK source or OEM binary is published.

## New firmware trace

Captured controller SHA-256 `71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`:

- Sink notification call `0xa7a4d4` dispatches virtual slot +0x24 through vtable `0x10574b0` to `0xa7c5c4`.
- The display session forwards to its task's slot +0x18 (`0xa7c624–0xa7c628`), resolving through vtable `0x1058f00` to `0xa837a8`.
- That task loops existing jobs, selects guidance type through `0xa86b10`, and stores it at job +0xc (`0xa838d8`). It does not create a pixel buffer or associate a TCP endpoint with one.

The captured active Screen config assigns gfx/video1 to display1 and video2/video3 to display2. Display2 is 800×480. Captured WFD/native callbacks reach OMAP scanout and a TDA19988 transmitter. This is a physical video-output path, separate from B009 control traffic. An inventory covers 48 distinct ELF captures and their dependencies/import boundaries; it is not a claim that every function was decompiled.

## Additional geometry difference and routing search

Follow-up: [native geometry trace](PIP-GEOMETRY-TRACE-2026-11-19.md) establishes that320×200 is our marker choice, not a measured factory source; there is no proven320→460 resize to implement. The reference starts Guidance only when the selected sink geometry exactly matches its native content profile (620×313 on its G30). Our retired helper posts 320×200, whereas retained Supra selection is 460×237. There is no verified scale/crop mapping between them. Simply connecting the new handshake to that helper would therefore skip a contract check enforced by the reference. Enlarging its PiP descriptor to 460 pixels would also exceed the retained 320×320 resource limit. Those sizes describe different domains until the receiver mapping is established.

A further bounded search covered 68 captured/reference artifacts. No exact ECU60 firmware-ID match or explicit TDA-output-to-HUD mapping was found. NBTCarHU names `DisplayController.DCARNBTAPIXHdcpControl` and `DisplayController.DSYSNBTPiaClientInterface`; captured `libnbthdcp.so` calls an `hdcp-sc` resource manager via devctl/pulses and exposes key/revocation/security callbacks. This does not establish pixel routing. No corresponding DisplayController or hdcp-sc executable was located in the retained output filenames. These are leads, not permission to alter HDCP or a request for another capture trip.

## Why the larger-display runner is still blocked

Three identifiers must not be conflated:

1. The owned TCP endpoint advertised in B009.
2. Native Screen output and the maneuver identity in its 84-byte metadata.
3. The receiver's image lookup and physical windshield destination.

The new transport implements (1). Existing native producer evidence covers posting for (2). Neither captured receiver code nor a working Supra implementation establishes the association to (3). The captured 460×237 selection is Kombi; it does not justify changing the 320×320 resource limit, the producer dimensions or the physical output selection. The 800×480 scanout is not a measured usable windshield canvas.

The actual cluster receiver executable remains absent. Head-unit boot IFS and HU graphics libraries are not that firmware. The earlier readback returned no firmware bytes. Further HU-side selector changes cannot stand in for its image lookup contract.

No car session is requested on this change. The failed `pip_trial.py --execute` stays retired. A next drawing candidate needs evidence tying an owned producer to a receiver image identity/destination, plus Guidance withdrawal, resource absence and local producer cleanup. The handshake module's close operation supplies only its own network cleanup. A plan or successful compile is not that proof.
