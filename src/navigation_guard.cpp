#include "navigation_guard.hpp"
namespace supra {
static unsigned u16(const unsigned char* p){return (unsigned(p[0])<<8)|p[1];}
static unsigned u32(const unsigned char* p){return (unsigned(p[0])<<24)|(unsigned(p[1])<<16)|(unsigned(p[2])<<8)|p[3];}
Traffic classifyTraffic(const unsigned char* b,size_t n,size_t wire,unsigned ownIp,unsigned ownPort,unsigned clusterIp){
 if(!b||n!=wire||n<14)return UnknownTraffic;
 unsigned type=u16(b+12),off=14;
 for(unsigned i=0;i<2 && (type==0x8100||type==0x88a8);++i){if(n<off+4)return UnknownTraffic;type=u16(b+off+2);off+=4;}
 if(type!=0x800)return type==0x8100||type==0x88a8?UnknownTraffic:IgnoreTraffic;
 if(n<off+20||(b[off]>>4)!=4)return UnknownTraffic;
 unsigned ihl=(b[off]&15)*4,total=u16(b+off+2);
 if(ihl<20||total<ihl||off+total>n)return UnknownTraffic;
 if(u32(b+off+16)!=clusterIp||b[off+9]!=6)return IgnoreTraffic;
 if(u16(b+off+6)&0x3fff)return UnknownTraffic;
 if(total<ihl+20)return UnknownTraffic;
 unsigned tcp=off+ihl,thl=(b[tcp+12]>>4)*4;
 if(thl<20||total<ihl+thl)return UnknownTraffic;
 if(u16(b+tcp+2)!=30502||total==ihl+thl)return IgnoreTraffic;
 // Exact factory transport keepalive is not a navigation-model write.
 // Split/combined-with-other-content packets still revoke conservatively.
 const unsigned char cookie[]={255,255,0,0,0,0,0,8,222,173,190,239,1,1,1,0};
 unsigned payload=total-ihl-thl;bool cookies=payload%16==0;
 for(unsigned i=0;cookies&&i<payload;++i)if(b[tcp+thl+i]!=cookie[i%16])cookies=false;
 if(cookies)return IgnoreTraffic;
 if(u16(b+tcp)==ownPort&&u32(b+off+12)==ownIp)return OwnTraffic;
 return FactoryTraffic;
}
}
