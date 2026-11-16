> Superseded readiness note: the lifecycle core now has a TCP transport and executable candidate drawing runner. See [LIVE-DRAWING-TEST.md](LIVE-DRAWING-TEST.md). The core alone still does not establish visual success.

# Distinct-session lifecycle component

16 November 2026. This is an executable, transport-injected lifecycle library,
not an executable or demonstrated windshield marker test. No vehicle was
connected and no live request was sent.

## Implemented behavior

`tools/ric_owned_session.py` combines the traced create, checkResource,
setResource, disposeResource and dispose operations into one stateful component.
It uses the existing strict encoders/decoders rather than a factory replay.

- Create is attempted once with an explicit distinct identity and version tuple.
- Every request has a new client/session request ID. Responses must match service,
  method, client ID, request ID, protocol/interface, size, success kind and code.
- Only a handle returned in that matching create response is retained. Zero,
  0xffffffff and the observed factory handle 200 are rejected. Additional known
  handles can be excluded. No arbitrary handle import or reconnect is provided.
- A lost create reply leaves allocation unknown. It is not retried or followed
  by a guessed disposal. A returned handle is retained before parsing its config
  so malformed configuration can still trigger an instance-release attempt.
- Resource existence is checked before upload; an existing resource is not
  overwritten. Upload intent is recorded before the request, so losing its reply
  does not bypass cleanup.
- Cleanup attempts resource disposal, a separate check of the same resource,
  and instance disposal. Failure of one step does not suppress later steps.
- Errors, a true post-dispose check, and an unknown result stay explicit in the
  cleanup report. Neither acknowledgement nor a false check becomes visual
  erasure. Repeated close does not resend cleanup requests.
- A context manager attempts cleanup when the application body raises an ordinary
  exception. Process termination, a broken transport, or an interrupted cleanup
  cannot be presented as guaranteed removal.

The injected transport must enforce the supplied per-request timeout. There is
no socket adapter or vehicle endpoint in this component; this work did not
silently enable a live sender. The bitmap method is resource-only. Its caller
still needs to establish resource/configuration semantics and the drawing graph;
a successful create response alone does not prove exclusive allocation policy.

## Failure-injection validation

Full suite: **175 tests pass**. Twelve new lifecycle tests cover the complete
synthetic sequence, lost upload reply, disposal failure, lost create reply,
factory-handle rejection, malformed returned configuration, refusing existing
resources, idempotent close, wrong response correlation, instance-release error,
invalid identity and cleanup after an application exception. Synthetic transport
responses test control flow, not the cluster's behavior or a visible marker.

## Public implementations reviewed

[The J29 guidance implementation](https://github.com/Sq00ky/Supra-iDrive6-Android-Auto/blob/be188f7f6ff37da724fdde765b01bdf9a48cc2f1/milestone-7/src/cluster/j29_graph.hpp)
and its adjacent template describe a 97-frame startup and six-frame cancellation
sequence. The implementation explicitly reuses the factory instance, defaults
to its observed handle, and excludes creation/disposal from the allowed methods.
It provides useful sequence evidence, but not an independent session contract.
Its cluster-side function-name reference did not lead to a published server
implementation in the reviewed repository. No template was copied into our app
or transmitted.

[The native-firmware emulator](https://github.com/agent00jackson/bimmulator/blob/bf03f2eed11969c1450a64fe5ba301a5ed128257/README.md)
targets an F32/Bosch BO03 6WB configuration. Its documentation requires externally
supplied, exact PSdZData firmware packages and says other vehicle variants are
not verified. It is not an available J29 renderer or a firmware-free way to test
this Supra. Nothing was installed or downloaded from a firmware distributor.

## Outcome and honest boundary

The requested actual independent-session drawing/removal test has **not been
achieved**. This component closes application-side failure-handling work but
cannot supply the server implementation, accepted visible model, or visual
outcome absent from the available material. A mock renderer would demonstrate
our assumptions, not the Supra's behavior. Additional decoder/test counts must
not be represented as a completed drawing test.

No further car visit is requested. Source and evidence are saved so this work can
be used when a verified independent rendering contract becomes available.
