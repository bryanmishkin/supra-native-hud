#ifndef SUPRA_FACTORY_BACKGROUND_HPP
#define SUPRA_FACTORY_BACKGROUND_HPP
#include <stddef.h>
namespace supra {
inline unsigned bg16(const unsigned char* p){return unsigned(p[0])*256+p[1];}
inline unsigned bg32(const unsigned char* p){return (unsigned(p[0])<<24)|(unsigned(p[1])<<16)|(unsigned(p[2])<<8)|p[3];}
// Only the measured background context and factory text namespace. Never permits
// guidance visibility, maneuver/road-image binding, bitmap ownership, or sessions.
inline bool backgroundFactoryRequest(const unsigned char* p,size_t n){
 if(!p||n<20||n>4096||bg16(p)!=0xb006||bg16(p+8)==0x5348||p[12]!=1||p[13]!=1||p[14]||p[15]||bg32(p+16)!=200)return false;
 unsigned method=bg16(p+2);
 if(method==4)return n==20; // Supervisor separately requires acknowledged idle state.
 if(method==8)return n==24&&(bg32(p+20)>>24)==3;
 if(method==2)return n==25&&(bg32(p+20)>>24)==3&&p[24]==3;
 if(method==9||method==3){
  if(n<38||bg32(p+25)!=n-33||bg32(p+20)!=bg32(p+33)||p[24]!=p[37])return false;
  if(method==9)return bg32(p+20)==0x11000000&&p[24]==17&&bg32(p+29)==1;
  return (bg32(p+20)>>24)==3&&p[24]==3&&bg32(p+29)==4;
 }
 return false;
}
}
#endif
