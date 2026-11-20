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
