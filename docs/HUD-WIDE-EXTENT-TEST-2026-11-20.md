# Narrow-tail extent test beyond the V1 image footprint

Offline executable candidate, 20 November 2026. V1 is unchanged. This uses the live-proven separate-entry windshield binding. It does not claim an editable root viewport or increased height.

## Why this differs from the completed tests

The completed pair used two 150x36 images. Both appeared side-by-side in the windshield, but the second was clipped. IMG_1998 shows the full first boundary and only part of the second. The cluster showed both complete images. This establishes delivery of the second entry, not its complete usable width or the cause of clipping.

The new case `wide_tail_64` keeps the first image exactly 150x36 and **changes the second uploaded resource to 64x36**. It preserves alignment0, the accepted two-entry graph, all support models, and the seven withdrawal commands byte-for-byte. It does not change a selector, substitute an image in a text cell, repeat the one-image control, or run Hz tests.

64 is a conservative candidate under the advertised 150x36 per-image maximum, not a measured receiver boundary. The receiver could scale, space or clip a narrower image differently. We must observe that rather than promise it fits.

The cyan first tile marks the simultaneous V1-sized reference. The amber second tile has three white vertical fiducials and a four-column green far-right rail. That rail distinguishes a complete narrow image from another half-image result. Combined source widths are214; this is **not** a claimed214-pixel physical viewport. The preview's gap is illustrative, not measured geometry.

## Exact acceptance

During the full30-second static window, record both displays. In the windshield, require:

1. The complete cyan V1-sized reference, including its right edge.
2. The amber tile spatially to its right, rather than overlapping/replacing the first.
3. All three white fiducials and the entire green far-right rail visible.

Only that combination demonstrates a complete second drawing region beyond the first image's footprint. It would support a wider two-panel V2 layout through this route. It would **not** establish free positioning, a taller canvas, arbitrary root drawing, or software control of the optical boundary.

If the second image remains clipped, disappears, overlaps, or scales into the original footprint, the expansion acceptance fails. Do not declare success from ACKs, allocated resource presence, source widths or cluster output. Do not automatically schedule more width/alignment sweeps. Keep the photograph and exact upload/graph journal for tracing the remaining constraint.

## Prepared implementation

- `road_extent_probe.py`: dimensioned150x36 and64x36 assets; no vehicle calls.
- `road_list_expansion_trial.py`: existing lifecycle, new named extent case; journals resource dimensions and image hashes.
- `manage_road_list_session.py prepare --extent-only`: a one-case batch, no historical control/alignment/Hz cases.
- Existing runner validates V1 files and stopped state, checks both owned slots8/9 absent, records uploads before send, performs all seven graph withdrawals before disposing images, and checks absence.
- A withdrawal failure retains resources for recovery rather than deleting a potentially referenced image. Visual clearance and final V1 restoration/runtime checks remain required.

The test uses no RPM or boost feed and makes no persistent application/install changes. It is an experiment, not a larger-canvas fix already verified in the car.

## Offline evidence

The new graph and cleanup compare byte-for-byte with the accepted separate-entry case. Both image buffers survive actual RLE32 encode/decode with their exact dimensions and green edge intact. The new case passes all29 lost-reply positions, both occupied-slot cases, cancellation and journal failure; the complete five-case lifecycle suite covers140 lost-reply positions. Thirteen road-related unit tests pass. These checks exercise code and injected transport responses, not physical receiver visibility.

Private prepared kit and source preview: `outputs/hud-wide-extent-2026-11-20/` in the workspace, archived to Drive. Captured profiles/packets remain private.

## Actual viewport-control investigation

The road-list wire model does not expose x/y/width/height/clip fields. Current evidence supports supplying differently sized resources and entries to a receiver-owned layout, not resizing its parent. [Consumer tracing](HUD-BOUNDARY-CONSUMERS-2026-11-20.md) rules out the alleged ExternalDisplay dimensions. PiP selection1 remains cluster-only; no traced input makes it select windshield0. Those unresolved mechanisms are separate from this concrete narrower-tail test and must remain explicit in the capability map.
