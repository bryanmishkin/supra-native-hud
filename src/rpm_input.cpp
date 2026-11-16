#include "rpm_input.hpp"
namespace supra {
bool applyRpmReply(Input& in,const unsigned char* p,size_t n,uint64_t requested,uint64_t received) {
    bool ordered=requested>=in.rpm.at;
    in.rpm.valid=false;
    if(!p || n!=4 || p[0]!=0x41 || p[1]!=0x0c || received<requested || received-requested>300 || !ordered)return false;
    in.rpm.value=(256.0*p[2]+p[3])/4.0;in.rpm.at=requested;in.rpm.valid=true;
    return true;
}
}
