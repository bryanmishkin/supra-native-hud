# HUD destination and image binding after the cluster success

V1 is unchanged. No vehicle operations or Hz tests in this analysis.

The corrected producer's visible cluster marker proves delivery of custom pixels to the cluster. It does not prove a larger windshield display. Its receiver-selected tuple was scale 1, 460×237, destination 1.

## Executed native facts

`verify_sink_destination_branch.py` executes controller 0xa7a228 with all four combinations of cached state and incoming selection, without intercepted calls. Selection 0 sets the internal HUD flag; selection 1 clears it. That flag selects the separately verified 8301/8402 HUD guidance types. Forcing 8402 metadata while the receiver selected 1 does not make the receiver choose the HUD.

`verify_sink_completion_origin.py` executes the completion construction. It copies selection from the current received notification and appends completion status. B009 method 1 is completion, not a destination setter. Do not falsify a completion with 0 to try to force windshield output.

The native producer's main-phase predicate accepts phases greater than 2. Both phases 3 and 4 qualify. The fourth distance threshold alone is not an established destination selector. See HUD-GUIDANCE-STAGE-TRACE.md.

## Cross-check of all saved captures

`audit_hud_selection_corpus.py` scans 82 classic PCAP files and preserves decoding errors. It finds ten selection-1 notifications and zero selection-0 notifications in the accepted TCP streams. This is not a claim about unparsed streams, UDP, or uncaptured intervals.

Thirteen exact detailed-picture messages have four distinct payloads but **one identical normalized shape** after removing only model ID and image reference. Factory messages use image FFFFFFFF; our tested message uses 02000004. Thus the recorded factory examples do not expose missing road geometry or another nonzero field in this 54-byte model that explains the difference. This does not prove that every receiver input or surrounding model is equivalent.

## Next-test admission

A larger-windshield test is not ready from these results alone. Its missing prerequisite is a supported input that causes the receiver to issue HUD selection 0, or a separately demonstrated windshield pixel path. A fabricated completion, local HUD flag, forced metadata type, or another threshold-only trial cannot stand in for that evidence.

The corrected marker remains a proven cluster transport control. Preserve its tested build and cleanup. A subsequent destination-capable producer must record the received tuple, adapt metadata and geometry to that tuple, and fail closed on an unsupported tuple; the current helper accepts only the measured cluster tuple. Do not label it a HUD-selection-capable runner.

These results eliminate concrete incorrect fixes; they do not establish receiver firmware behavior that has not been recovered. No new car visit is requested by this document.
