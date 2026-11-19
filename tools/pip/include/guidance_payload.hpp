// Native-verified DNAVIManeuverView payloads. No network or drawing operations.
#ifndef SUPRA_GUIDANCE_PAYLOAD_HPP
#define SUPRA_GUIDANCE_PAYLOAD_HPP
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <vector>
#include <utility>
#include <stdexcept>
namespace supra_pip {
typedef std::vector<uint8_t> GuidanceBytes;
inline void guidance_u32(GuidanceBytes& out,uint32_t value) {
    for(unsigned i=0;i<4;++i)out.push_back(uint8_t(value>>(8*i)));
}
inline void guidance_text(GuidanceBytes& out,const std::string& value) {
    if(value.size()>4096 || value.find('\0')!=std::string::npos)
        throw std::invalid_argument("Guidance string exceeds local budget or contains NUL");
    guidance_u32(out,uint32_t(value.size()));
    out.insert(out.end(),value.begin(),value.end()); // no terminating NUL or alignment padding
}
inline GuidanceBytes register_guidance(uint32_t maneuver,uint32_t type,unsigned style=3) {
    if(type>0xffffffu || style>0x7fu)throw std::invalid_argument("Guidance type/style out of range");
    GuidanceBytes out;guidance_u32(out,maneuver);guidance_u32(out,type|(style<<24));return out;
}
inline GuidanceBytes attach_guidance(uint32_t guidance,uint32_t displayable) {
    GuidanceBytes out;guidance_u32(out,guidance);guidance_u32(out,displayable);return out;
}
inline GuidanceBytes register_displayable(uint32_t user,uint32_t type,uint32_t width,uint32_t height,
        const std::vector<std::pair<std::string,std::string> >& options) {
    if(options.size()>32)throw std::invalid_argument("Local option budget exceeded");
    GuidanceBytes out;guidance_u32(out,user);guidance_u32(out,type);guidance_u32(out,width);
    guidance_u32(out,height);guidance_u32(out,uint32_t(options.size()));
    for(size_t i=0;i<options.size();++i){guidance_text(out,options[i].first);guidance_text(out,options[i].second);}
    return out;
}
inline GuidanceBytes set_ric_maneuver_content(uint32_t guidance,uint32_t ric) {
    char text[48];snprintf(text,sizeof(text),"RICManeuverID=%ld",static_cast<long>(static_cast<int32_t>(ric)));
    GuidanceBytes out;guidance_u32(out,guidance);guidance_u32(out,1);guidance_u32(out,5);
    guidance_u32(out,7);guidance_text(out,text);return out;
}
inline GuidanceBytes unregister_guidance() { return GuidanceBytes(); }
inline GuidanceBytes unregister_displayable() { return GuidanceBytes(); }
struct GuidanceRequest {
    uint32_t request_type, event_id, sequence;
    GuidanceBytes payload;
    GuidanceRequest(uint32_t t,uint32_t e,uint32_t s,const GuidanceBytes& p)
      :request_type(t),event_id(e),sequence(s),payload(p) {}
};
// Caller allocates sequence from its live framework. Both requests MUST use
// the same owned client route and sequence; this helper performs no I/O.
inline std::vector<GuidanceRequest> displayable_handshake(uint32_t sequence,
        uint32_t user,uint32_t type,uint32_t width,uint32_t height,
        const std::vector<std::pair<std::string,std::string> >& options) {
    if(!sequence)throw std::invalid_argument("Owned registration sequence must be nonzero");
    std::vector<GuidanceRequest> out;
    out.push_back(GuidanceRequest(0x105u,0x80000004u,sequence,GuidanceBytes()));
    out.push_back(GuidanceRequest(0x100u,4,sequence,register_displayable(user,type,width,height,options)));
    return out;
}
// Only after the caller has completed its owned pixel-removal protocol.
// These requests are NOT acknowledgments of visible-image removal.
inline std::vector<GuidanceRequest> displayable_release_requests(uint32_t sequence) {
    if(!sequence)throw std::invalid_argument("Owned registration sequence must be nonzero");
    std::vector<GuidanceRequest> out;
    out.push_back(GuidanceRequest(0x106u,0x80000004u,sequence,GuidanceBytes()));
    out.push_back(GuidanceRequest(0x100u,6,sequence,GuidanceBytes()));
    return out;
}
// Keep the originating registration sequence in the envelope; never put it in payload.
}
#endif
