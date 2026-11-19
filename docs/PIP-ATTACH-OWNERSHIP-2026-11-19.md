# PiP attachment ownership and picture identity

Offline native evidence; NavNBTEvoController SHA256 71b2813f6ae243f3a01d8b134cc6aaddf47aa32b6b712d1202085d68e246f04a and NavigationFully SHA256957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d.

## Origin of command guidance session ID

Job sendAttachCall0xaa0164 receives an existing maneuver object pointer. It invokes0xaa0120 with the job's helper+0x148, address of observer field+0x168, and that object pointer. If the observer is absent,0xaa00c8 allocates/initializes a typed internal event object through0xa9f294 and0xaa0088.0xa9f59c stores the maneuver pointer at observer+0xc and registers the observer through0xa94adc on the object's+8 interface. The following attach call0xa9f2a4/0xa9f5ec binds the same object.

The returned MyCommandDataNotification handler accepts only the exact observer pointer stored at job+0x168 (0xaa094c–54). It copies payload+0x1b4 into job+0x28 and processes the data. Thus the guidance session ID comes from the registered command-data source, not an arbitrary caller-chosen integer or the B006 create handle.

Successful attach sets job+0x16c when no sink switch is pending (0xaa01e8–f4). A separate setter0xa9efec controls switch flag+0x16d. Processing first stages PiP metadata; subsequent attach/switch notification requires its pending flag and nonzero guidance session ID.

## Exact notification consumer

Attach observer0xa9f094 emits two u32 values: job maneuver ID+8 and guidance-session ID+0x28. Switch observer0xa9f0f8 emits the same pair. Manager attach handler0xa7644c passes payload+4 (guidance-session ID) to sendPlayToICHUD0xa76398. That invokes display session manager+0x70 virtual+0x20, passing the manager's current maneuver ID+0x74 and supplied guidance-session ID. This reaches the previously resolved displayable job matching and AttachGuidanceSession/SetContent path.

These calls are internal object/event APIs with real object ownership. They are not a demonstrated public DSI/SOME-IP sequence constructible from B006+B009 alone. No generated standalone client/IDL for this path is in the project source. This does not prove such an interface cannot be reverse engineered; it identifies exactly which registration and object correlation are not yet externally implemented. Do not invoke captured pointers from another boot or force pending flags.

## Picture ID and resource ID are different

HG picture ID becomes original resource ID+4. Constructor0xa426dc initializes converted resource IDs+0x10/+0x14 toUINT_MAX. IC conversion0xaacac4 obtains a free ID from the PiP resource pool (model+0x1330), removes it through0xa660f4, stores it at+0x14, and records a converted-ID/original-ID pair. Empty pool leaves no new usable mapping. This is dynamic allocation, not proven base+pictureID arithmetic. That map is controller-local; its existence does not prove a receiver-side association to pixels.

NavigationFully CGVView0x61e384 increments context+0x54 through setter0x7de30c. The same field supplies HG picture ID and low16 bits of the native metadata record. Native execution verifies1→2,2→3,65535→65536,UINT_MAX→0. The old custom producer's incrementing present counter is therefore not disproven by the factory's retained IDs2/3. Exact increment cadence and pixel/descriptor synchronization remain separate questions.

Supporting files: pip-attach-owner-*.json, pip-command-observer-*.json, attach-notification-consumer.json, pip-id-conversion.json, native-picture-counter.json, verify_pip_picture_counter.py. V1 untouched; no vehicle operations.
