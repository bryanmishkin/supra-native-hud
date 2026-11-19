# Native PiP metadata differs for the HUD style group

This is a producer-contract finding from executed captured code, not an inventory update. V1 and the vehicle are untouched. No larger-display success is claimed.

## Exact difference recovered

Both native junction and intersection renderers construct an84-byte metadata record. Junction0x7ee5a0–0x7ee5c4 and intersection0x7f646c–0x7f6490 set **record byte7** to:

```
((guidance_type / 1000) & 255) == 8 ? 0 : 1
```

Thus actual selected HUD types8301/8402 have value0;4301/4402 and5301/5402 have value1. This is not the B009 selection byte: it is inside the pixel metadata record. The receiver's interpretation of that byte has not been executed or recovered.

The retained native selector separately associates8301/8402 with its HUD branch. Taken together, this establishes a producer-side distinction that the fixed G30-derived marker template does not parameterize. It does not prove changing one byte will overcome the missing sink/physical-output association.

## Complete record construction now verified

`pip_metadata_record.py` implements the bounded native record structure:

- little-endian picture counter at2;
- byte4=1;
- byte5 from maneuver option-map key0;
- byte6 is the inverse of the resolved native style predicate;
- byte7 computed from guidance type as above;
- little-endian RIC maneuver identity at16;
- remaining bytes initialized to zero in this examined construction path.

The builder requires the style predicate as an explicit boolean. It rejects style-client bits passed as an unmasked guidance type. It returns the native record or the already-verified rotated CPU upload; it deliberately does not assume a framebuffer channel conversion or claim receiver attachment.

`verify_pip_metadata_record.py` executes both complete factory construction regions for32 combinations of guidance type, style predicate and option value. All84bytes match the new builder. Native initializer, style accessor, option-tree lookup and setter execute. Only current-maneuver lookup, signed division and memcpy ABI boundaries are supplied. This is more than checking a rewritten formula against itself.

`verify_pip_destination_metadata.py` independently executes26 boundary/type cases in both renderer branches. These prove the group comparison, including8000/8999/9000 boundaries.

## Actual image-upload API traced

The old diagnostic string says `VG_sABGR_8888`, but the captured implementation routes `imageSubData` through NGE CImageManager to **glTexSubImage2D** at0x8b1c10.

Actual native format selector0x935250 returns GL_RGBA(0x1908) for image format0. Native upload setup0x8b1b7c passes21×1, GL_RGBA, GL_UNSIGNED_BYTE(0x1401) and the unchanged rotated84-byte upload pointer. The argument observer verifies three producer records. It intercepts texture binding and GL calls; it does not simulate a GPU or validate scanout.

Therefore record byte7 appears at CPU-upload byte6 after the native per-word rotation. A conventional RGBA-to-BGRA pixel conversion would place it at BGRA byte4. The retired marker hardcodes BGRA byte4=1. That is a **specific mismatch candidate for a HUD-group profile**, conditional on proving the final framebuffer conversion and actual selected producer profile. It is not a proven live root cause.

## Consequence for the next implementation

A replacement producer must derive metadata from the actual selected view and owned maneuver identity, rather than treating the G30 maneuver template as universal. It must also honor the owned sink negotiation, actual packing and image association. The new builder resolves the producer-record portion; it does not resolve the receiver's lookup or grant a larger surface.

The old marker runner remains retired, installed V1 is unchanged, and no car session is requested. A test claiming to draw V2 in the large space is not yet ready.

## Reproduction

Run with the retained analysis environment and exact NavigationFully SHA256957528a9f37a026fd7737f59ca5f96247ed606d49deb2efe79400d624f439f4d:

```
python tools/verify_pip_destination_metadata.py /private/NavigationFully
python tools/verify_pip_metadata_record.py /private/NavigationFully
python tools/verify_pip_metadata_gl_upload.py /private/NavigationFully
python -m unittest discover -s tests -p 'test_pip_metadata_record.py'
```

No OEM binary or shader source is included in GitHub. Attribution for the earlier reference envelope remains with ryseek and the contributors listed in THIRD_PARTY_NOTICES.md.

## The metadata draw does not blend away its low-valued channels

Further native execution follows the image draw at `0x8b1910–0x8b19cc` and the selected color-uniform writer at `0x8af08c`. For format 0, an image with alpha processing disabled and full draw opacity selects shader object `0x1df7fa4`, disables blending, and supplies an additive uniform of exactly `(0, 0, 0, 0)`. The shader object's constructor at `0x8addc0` selects the image fragment shader at `0xa66bc0`. Inspection of that shader shows a texture sample plus the additive color, without a channel permutation. The native uniform writer subtracts one from normalized opacity; treating its incoming 255 as an additive alpha of one would have been incorrect.

`verify_pip_metadata_draw_state.py` executes three alpha/opacity cases and observes the state setters and GL uniform arguments. It does not execute a GPU. The supplied state matches the metadata-image constructor, which passes zero for the alpha-processing flag. This closes the shader/blending portion of the metadata trace; it does not prove final scanout or receiver selection.

The captured `wsegl-screen.so` additionally maps native image format 8 and 9 to WSEGL format 2 in its switch at `0x25ec`, with the shared case at `0x272c`. Final memory-channel interpretation still needs to be tied to this exact driver ABI rather than inferred from the Screen format name alone. The QNX [pixel-format documentation](https://qnx.com/developers/docs/6.6.0_anm11_wf10/com.qnx.doc.screen/topic/manual/rscreen_window_pixel.html) describes RGBA8888 but does not specify the byte ordering needed here.

Validation: 52 PiP Python tests passed. The new native draw-state verifier passed all three cases separately. Installed V1, persistent startup, and the retired live-test guard were not changed.
