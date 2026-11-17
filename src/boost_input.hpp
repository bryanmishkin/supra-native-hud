#ifndef SUPRA_BOOST_INPUT_HPP
#define SUPRA_BOOST_INPUT_HPP
#include "hud_core.hpp"
#include <stddef.h>
namespace supra {
// Candidate conversions corroborated only at one near-ambient operating point.
// Exact UDS positive reply, original request timestamp and bounded latency.
inline bool pressureCandidate(Sample& out,unsigned did,const unsigned char* p,
                              size_t n,uint64_t requested,uint64_t received) {
    out.valid=false;
    if(!p||n!=5||p[0]!=0x62||p[1]!=(did>>8)||p[2]!=(did&255)
       ||received<requested||received-requested>100||requested<out.at)return false;
    unsigned raw=unsigned(p[3])*256+p[4];
    if(raw==0||raw==65535||(did!=0x4201&&did!=0x4205))return false;
    double value=raw/(did==0x4201?256.0:128.0);
    if(did==0x4201?(value<50||value>120):(value<=0||value>400))return false;
    out.value=value;out.at=requested;out.valid=true;return true;
}
struct BoostCandidate {
    Sample absolute,ambient;
    bool valid() const {return absolute.valid&&ambient.valid;}
    void apply(Input& in) const {in.manifoldKpa=absolute;in.ambientKpa=ambient;}
};
}
#endif
