# Batched output-driver capture

Prepared 18 November 2026 on v2-ux. This is a read-only research session, not a V2 drawing test or installation. V1 baseline v1-baseline-2026-11-18 remains installed and enabled.

## Purpose and evidence

Resolve the missing output side of the PiP investigation: capture the actual WFD driver, all neighboring graphics modules/configurations, running compositor maps, native display descriptors and LayerManager routing. The prior local texture and 21×1 metadata findings do not establish a larger windshield surface. Successful collection is evidence completeness for this batch, not proof of pixel transport or permission to draw.

## Before connection

Use the analysis Python environment with pyelftools. Run `python tools/capture_output_driver.py` for the offline plan. Run the output-driver and consolidated-capture tests. Preserve the current branch and baseline JSON. No QNX rebuild, car upload, restart, factory navigation exercise, or V1 pause is required.

## At the car

1. Park, connect ENET and wake iDrive. Engine operation is not required for these file reads; if already outdoors and idling, leave it unchanged. Keep guidance and radio selector closed where practical.
2. Discover the current adapter/source address and head-unit address; verify the saved SSH host identity. Do not reuse historical process IDs. If SSH is unavailable, handle temporary access separately; this runner never unlocks it.
3. From the repository, run with verified values and a fresh private output directory:

```sh
python tools/capture_output_driver.py --execute \
  --head "$HEAD" --local "$LOCAL" --known-hosts "$KNOWN_HOSTS" \
  --socket "$SSH_SOCKET" --output "$CAPTURE_DIR"
```

4. The runner checks the 13 baseline files and two live startup configurations before proceeding. It captures permanent fault snapshots; all graphics-directory `.so`/versioned `.so` and `.conf` files; symlink inventory; LayerManager and screen process maps; recursively needed libraries; process arguments; native display 1/2 descriptions; LayerManager screen 0/1 and surface 1056; interfaces/routes. Static files must match two reads (or a freshly verified cached read). Transfers are bounded at 64 MiB/file, 512 MiB/session and 20 minutes.
5. Before unplugging inspect `manifest.json`: `capture_complete` must be true, missing empty, both V1 snapshots must have all 15 matches, fault records unchanged, local hash audit passed. If a command fails or capture raises, the run is incomplete even if an intermediate manifest exists. Do not call an interrupted run successful.
6. **While still connected**, inspect the newly captured graphics configs and process arguments for output modules/config includes outside the graphics directory; compare native display inventory to the two saved descriptors. Capture any additional referenced output components with the existing bounded `Session.file` helper and close their dependencies. A missing or ambiguous display route remains explicit; no guessed display IDs or write commands. This review is required before declaring the batch sufficient.
7. Check runtime acceptance/heartbeat snapshots and ask whether V1/factory displays remain normal (if HUD visible). Set the human observation in the session notes; the tool deliberately leaves `human_display_check_pending` true. No unnecessary radio/navigation repetition.
8. Save raw bytes privately, hash the archive, upload to Drive, and commit only findings/tooling to GitHub. Factory binaries, profiles, credentials and captures must never enter Git.

## Boundaries

No vehicle writes, mounted-filesystem changes, token edits, signals, process stops, framebuffer reads, drawing or SSH activation are performed. `LayerManagerControl` is used only for `get` queries. The saved `list screen` footer is known unreliable; direct screen 0/1 reads and native descriptors are retained independently. No claim is made that local screen 1 equals the windshield.

If this evidence exposes a transport contract, prepare a separate bounded drawing/removal test offline. This capture cannot guarantee that proprietary receiver behavior will be fully resolved without further analysis.
