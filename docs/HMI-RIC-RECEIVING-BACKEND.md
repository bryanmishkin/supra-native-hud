# Captured HMI RIC receiver and image-target meanings

Offline native analysis,20November2026. V1 and vehicle state unchanged. This documents a head-unit receiving implementation; it is not the cluster's windshield compositor.

## A concrete RIC consumer exists in HmiMain3D

The captured HMI contains CommonAPI `RICServiceGuidanceSomeIPStubAdapter` and concrete `CRbCommonApiRicBackend`, not only client serializers. The adapter's road-data handler at0x2847fb0 invokes the implementation registered at adapter+0x98, virtualslot0x3c. The concrete override0x25b6ae4 forwards models through0x25f9c68 to `CRbRicModelManager::putModelRoad` at0x260edb0. Variant2 is stored through0x261f254; variant1 through0x261f594. Other variants enter an unsupported-model path.

The implementation is HMI roadbook/splitscreen/pad code. Its local model acceptance does not establish the same layout, clipping or code on the Supra cluster receiver.

## HighGuidingImageInfo target is explicitly an HMI destination

Actual consumer writer0x2603778 reads `imageTarget` from object+0x18 and resolves names through0x25b8f98. The initializer at0x25b8df0 builds this table:

| Value | Native name |
| --- | --- |
|0|NONE|
|1|HMI_ROADBOOK_SPLITSCREEN|
|2|HMI_ROADBOOK_PAD|
|3|HMI_GUIDING_LABELS_MAP|

`imageContentType`, object+0x1c, uses0x2602904 and initializer0x2602760:

| Value | Native name |
| --- | --- |
|0|DEFAULT|
|1|INTERSECTION_VIEW|
|2|BRANCH_VIEW|
|3|BRANCH_REALISTIC_VIEW|

`tools/verify_hmi_image_target_tables.py` executes both actual table-construction blocks with no intercepted calls and checks all eight values/names. It requires the private HMI binary with pinned SHA256 `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935`.

These target values must not be reinterpreted as B009 windshield/cluster selection values. The retained Supra B006 configuration does not advertise model50, so the serializer and named table do not admit sending that model to the car.

## Local clipping is not windshield clipping

HMI function0x16d62e8 obtains `roadbookClippingRectangleX/Y/W/Z`. Actual instructions0x16d6644..0x16d66a8 scale an input rectangle using configured width/height divided by540, then add configured x/y. Two bounded actual-code cases verify the arithmetic and adjacent-memory guards without intercepts. Its callers use nominal(0,55,540,90) and(0,55,540,55) rectangles in lane-guiding/perspective code.

The540-unit basis and these heights belong to this local HMI path. No link to the Ethernet receiver's root framebuffer, optical HUD extent or parent clip has been demonstrated. No live resize command follows from this result.

## Output-owner follow-up: registration and event direction

The concrete backend is instantiated at `0x25b676c`: the caller passes the literal `BMW.NBTEvo` at `0x25b6798` into `createInstance` (`0x25b7718`). That function constructs the CommonAPI address with `local:%s:%s` at `0x25b781c` and the caller-provided instance, then attempts service registration at `0x25b7a20`. Its success/failure paths explicitly log RIC CommonAPI service registration. This identifies the head-unit service instance; it does not identify the cluster receiver or a Screen window.

The visibility callback has also been followed beyond its label. Backend vtable `0x3125d80`, slot `+0x14`, contains `0x25b8018`. `CRbRicBackendBase::uiVisibilityChange` invokes that slot at `0x25fae1c`. The concrete implementation names itself `displaySwitchEvent`, logs “Notifying navigation about uiVisibilityChange”, constructs a CommonAPI event, then dispatches through the stub at backend `+0x20`, slot `+0x64` (`0x25b8194`–`0x25b8208`). This is a notification toward Navigation, not a pixel-output or physical-display setter.

Likewise, the traced clipping continuation `0x16d8798` packages a floating property value and invokes the supplied property object's virtual slot `+0x0c`. It does not directly call a Screen, LayerManager or Ethernet pixel-output API. We have not resolved that generic property object's concrete runtime owner. It would be incorrect to present this as proof that the local roadbook rectangle is attached to the main physical display, or to the windshield.

These follow-up edges are static native call/vtable evidence. The earlier enum construction and rectangle arithmetic are the portions executed under bounded emulation. No full scene, CommonAPI registration or physical scanout was emulated. No Ethernet HUD output owner was found in this bounded backend chain. The unresolved receiver-specific edge remains the cluster's interpretation and parent clipping of the accepted guidance models; this HMI service instance is not evidence of that implementation, and supplies no justified new live setter or repeat test.
