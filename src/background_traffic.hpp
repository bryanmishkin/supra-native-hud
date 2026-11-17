#ifndef SUPRA_BACKGROUND_TRAFFIC_HPP
#define SUPRA_BACKGROUND_TRAFFIC_HPP
#include "factory_background.hpp"
#include <vector>
#include <algorithm>
#include <map>
#include <string>
#include <stdint.h>
namespace supra {
// Each permitted byte is supplied by the supervisor BEFORE factory transmission.
// TCP fragments are matched against those exact bytes, never guessed from a
// plausible SOME/IP header inside arbitrary payload data.
class BackgroundTraffic {
 typedef std::vector<unsigned char> Bytes;
 struct Flow {bool begun;uint32_t next;Bytes history,pending;Flow():begun(false),next(0){}};
 std::vector<Bytes> authorized_;std::map<std::string,Flow> flows_;size_t bytes_;
 bool drain(Flow& f){
  static const unsigned char cookie[]={255,255,0,0,0,0,0,8,222,173,190,239,1,1,1,0};
  while(!f.pending.empty()){
   bool prefix=false;size_t c=f.pending.size()<16?f.pending.size():16;
   if(std::equal(f.pending.begin(),f.pending.begin()+c,cookie)){
    if(f.pending.size()<16)return true;
    f.pending.erase(f.pending.begin(),f.pending.begin()+16);continue;
   }
   bool consumed=false;
   for(size_t i=0;i<authorized_.size();++i){Bytes& a=authorized_[i];size_t count=f.pending.size()<a.size()?f.pending.size():a.size();
    if(!std::equal(f.pending.begin(),f.pending.begin()+count,a.begin()))continue;
    if(f.pending.size()<a.size()){prefix=true;continue;}
    f.pending.erase(f.pending.begin(),f.pending.begin()+a.size());bytes_-=a.size();authorized_.erase(authorized_.begin()+i);consumed=true;break;
   }
   if(consumed)continue;
   return prefix;
  }
  return true;
 }
public:
 BackgroundTraffic():bytes_(0){}
 bool authorize(const unsigned char* p,size_t n){
  if(!backgroundFactoryRequest(p,n)||bg32(p+4)!=n-8||authorized_.size()>=128||bytes_+n>524288)return false;
  Bytes b(p,p+n);for(size_t i=0;i<authorized_.size();++i)if(authorized_[i]==b)return false;
  authorized_.push_back(b);bytes_+=n;return true;
 }
 bool consume(const unsigned char* b,size_t n,size_t wire){
  if(!b||n!=wire||n<14)return false;unsigned type=bg16(b+12),off=14;
  for(unsigned i=0;i<2&&(type==0x8100||type==0x88a8);++i){if(n<off+4)return false;type=bg16(b+off+2);off+=4;}
  if(type!=0x800||n<off+20||(b[off]>>4)!=4||b[off+9]!=6)return false;
  unsigned ihl=(b[off]&15)*4,total=bg16(b+off+2);if(ihl<20||total<ihl+20||off+total>n||(bg16(b+off+6)&0x3fff)||bg32(b+off+16)!=0xa030c760)return false;
  unsigned tcp=off+ihl,thl=(b[tcp+12]>>4)*4;if(thl<20||total<ihl+thl||bg16(b+tcp+2)!=30502)return false;
  size_t len=total-ihl-thl;if(!len)return true;const unsigned char* p=b+tcp+thl;uint32_t seq=bg32(b+tcp+4);if(b[tcp+13]&2)++seq;
  std::string key((const char*)b+off+12,8);key.append((const char*)b+tcp,4);
  if(!flows_.count(key)&&flows_.size()>=16)return false;Flow& f=flows_[key];
  if(!f.begun){f.begun=true;f.next=seq;}
  int32_t delta=(int32_t)(seq-f.next);if(delta>0)return false;
  if(delta<0){size_t overlap=(uint32_t)(f.next-seq),check=overlap<len?overlap:len;if(overlap>f.history.size())return false;
   if(!std::equal(p,p+check,f.history.end()-overlap))return false;
   if(overlap>=len)return true;p+=overlap;len-=overlap;
  }
  if(f.pending.size()+len>65552)return false;
  f.next+=len;f.history.insert(f.history.end(),p,p+len);if(f.history.size()>65552)f.history.erase(f.history.begin(),f.history.end()-65552);
  f.pending.insert(f.pending.end(),p,p+len);return drain(f);
 }
 size_t pendingAuthorizations()const{return authorized_.size();}
};
}
#endif
