// Offline codec conformance executable: no network, Screen or vehicle access.
#include <stdio.h>
#include "native_metadata_record.hpp"
int main() {
    const unsigned types[]={4402,5402,8301,8402};
    unsigned char out[84];
    for(unsigned t=0;t<4;++t) for(int style=0;style<2;++style) {
        supra_pip::MetadataInput x={types[t],1,0x0f000004,0,style};
        if(!supra_pip::native_metadata_bgra_framebuffer(out,sizeof(out),x)) return 1;
        if(out[4]!=(types[t]/1000==8?0:1) || out[5]!=!style ||
           out[16]!=0x0f || out[19]!=4) return 2;
        printf("type=%u style=%d bgra=",types[t],style);
        for(unsigned i=0;i<84;++i) printf("%02x",out[i]);
        puts("");
    }
    return 0;
}
