> **Historical research / stage-specific evidence.** Preserved as recorded; “current,” “remaining,” and “next test” below refer to that earlier stage, not today. For the installed app use [verified status](APP-STATUS.md) and [current installation/rollback](PERSISTENT-INSTALL.md). Do not execute this older runbook as the persistent install procedure.

# Distinct session preparation and resource checks

Offline analysis, 16 November 2026. Controller SHA256:
`71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a`.

## New protocol-level verification step

B006 **method 2, checkResource** takes a nine-byte request:

- u32 big-endian instance handle;
- u32 big-endian resource ID;
- u8 resource type, 0..11.

A successful response has exactly one byte: Boolean 0 or 1. An error, timeout, missing response or empty acknowledgement is not Boolean false.

Static anchors: request sets method 2 at `0xba94e0`; body serializer `0xba937c` calls `0xba2ff0` twice, then resource enum `0xba8128`. Response handler `0xbc6160` calls `0xbc615c` -> Boolean reader `0xbc60d4`, which validates values 0..1.

## Actual captured behavior

All 144 saved stream files contain eight check requests and eight one-byte successful responses; no method-1 create or method-7/8 dispose message appears in those files. Six checks belong to the consolidated navigation recording. These six are now matched uniquely to responses using reversed endpoint tuples, client/session request IDs and capture timestamps. Stream hashes are verified against the saved inventory. The remaining two older checks were counted, not correlated by this run.

For one factory resource, the time-ordered recording shows:

1. Check request, followed by a matched **false** reply.
2. Resource upload, followed by an empty successful upload response.
3. Two later check requests, each with a matched **true** reply.

The other three matched checks return false before their resources are uploaded. This supports a resource-availability interpretation. It is not a post-disposal experiment. The uploaded resource is the previously decoded type-3 / variant-4 factory resource, **not** a custom bitmap.

The captured TCP boundary flag is false, so the report does not claim a complete connection epoch. Uniqueness is required within the retained recording. Duplicate/reused request IDs, missing counterparts and inconsistent/missing timing remain unresolved rather than guessed.

## Why factory callback completion is insufficient

The factory success callback at `0xaaf934` logs the Boolean but then copies resource ID (+0x14) into owner+0x84, clears owner+0x88 and notifies observers through `0xaaf474`. Error callback `0xaaf8d8` performs the same observed ID/flag updates and notification. This local completion path must not be reused as evidence that a resource exists, disappeared or was erased from the windshield. Our codec preserves the actual reply Boolean and distinguishes error results as null.

Resource disposal still uses method 8 with handle and resource ID, and instance disposal uses method 7 with handle. A later uniquely matched check could establish what the server reports about that resource after a disposal request. Even a false check would not prove that a cached rendered image has disappeared. Visual removal and independent-session semantics remain unverified.

## Our own session: prepared, not granted

`encode_distinct_create_body` now prepares the already traced create-body format with three explicit printable ASCII identity strings and three explicit version words. It rejects the two known factory roles, BMW.IC.Guidance and BMW.HMI.Roadbook. It does not choose a factory handle, pretend that another identity is accepted, or guess that protocol version words are our app's version. There is no network sender.

An actual distinct-client transaction must obtain its handle and configuration from its own successful create response. A synthetic create reply or a factory initialization is not such a grant. The captured head-unit client cannot establish the cluster's acceptance policy for a new identity; no create exchange is present in the saved streams.

## Concrete test sequence, with remaining boundaries

The eventual bounded drawing test must distinguish these outcomes:

1. Own create response: correlate it to our explicit candidate identity and inspect returned configuration. No factory identity/handle substitution.
2. Upload and reference: use IDs allowed by that configuration and the complete required model graph, then establish visible output. The full required bitmap graph is still not demonstrated.
3. Remove model references, then dispose the owned resource. Preserve failure results rather than silently clearing success state.
4. Check that same resource using the same live instance, correlate the Boolean response, and separately verify that the image is no longer visible.
5. Dispose the instance and record its response. Disconnect/process exit is not a proved cleanup mechanism.

This is more precise than treating an empty disposal response as cleanup. It is still **not an executable independent windshield drawing test**. No new car session is requested, no packet was transmitted, and no current vehicle access is assumed.

## Implementation and checks

- `tools/ric_resource_check.py`: strict request/reply decoder; explicit nine-byte check encoder; distinct-client create-body encoder. Errors never become false.
- `tools/ric_exchange_audit.py`: passive recording-based correlation with file hash/path checks, flow reversal, unique request IDs and timestamp checks. No cross-directory merging or network access.
- **163 tests pass**. New tests cover fixed wire vectors, truncation, Boolean/error distinction, factory-role rejection, identity/version bounds, unique pairing, different flows/IDs, duplicates, timing, file hash validation and path containment.
- Private evidence in `ric-removal-trace/`: address-labelled traces, all-stream counts, six matched transactions, resource timeline and tests. OEM data remains outside GitHub.

Example for an existing recording only:

```
python3 tools/ric_exchange_audit.py /private/recording/inventory.json
```
