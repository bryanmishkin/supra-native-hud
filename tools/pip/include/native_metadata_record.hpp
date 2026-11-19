#ifndef SUPRA_NATIVE_METADATA_RECORD_HPP
#define SUPRA_NATIVE_METADATA_RECORD_HPP
#include <stdint.h>
#include <stddef.h>

namespace supra_pip {
// Producer metadata derived from both captured native renderers. These inputs
// describe an OWNED producer; this codec does not create a receiver attachment.
struct MetadataInput {
    uint32_t guidance_type, picture, maneuver_id, option_zero;
    int style_flag; // 0 or 1; -1/unresolved must fail, never choose a default.
};
inline bool native_metadata_record(uint8_t* out, size_t size, const MetadataInput& x) {
    if (!out || size < 84 || x.guidance_type > 0xffffffu ||
        x.picture > 0xffffu || x.option_zero > 255u ||
        (x.style_flag != 0 && x.style_flag != 1)) return false;
    for (unsigned i=0;i<84;++i) out[i]=0;
    out[2]=uint8_t(x.picture); out[3]=uint8_t(x.picture>>8);
    out[4]=1; out[5]=uint8_t(x.option_zero);
    out[6]=uint8_t(!x.style_flag);
    out[7]=uint8_t(((x.guidance_type/1000u)&255u)!=8u);
    for (unsigned i=0;i<4;++i) out[16+i]=uint8_t(x.maneuver_id>>(i*8));
    return true;
}
inline bool native_metadata_rgba_upload(uint8_t* out, size_t size, const MetadataInput& x) {
    if (!out || size < 84) return false;
    uint8_t record[84];
    if (!native_metadata_record(record,sizeof(record),x)) return false;
    for (unsigned i=0;i<84;i+=4) {
        out[i]=record[i+1]; out[i+1]=record[i+2];
        out[i+2]=record[i+3]; out[i+3]=record[i];
    }
    return true;
}
// Native Screen format8 -> WSEGL2 -> IMGformat0x14 stores BGRA bytes.
// The captured readback converter swaps R/B to return GL_RGBA; this is its
// inverse for CPU-filled buffers. It does not prove physical scanout routing.
inline bool native_metadata_bgra_framebuffer(uint8_t* out, size_t size, const MetadataInput& x) {
    if (!out || size < 84) return false;
    uint8_t rgba[84];
    if (!native_metadata_rgba_upload(rgba,sizeof(rgba),x)) return false;
    for (unsigned i=0;i<84;i+=4) {
        out[i]=rgba[i+2]; out[i+1]=rgba[i+1];
        out[i+2]=rgba[i]; out[i+3]=rgba[i+3];
    }
    return true;
}
}
#endif
