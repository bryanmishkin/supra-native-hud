#include "factory_lease.hpp"
#include <cstring>
namespace supra {
static unsigned u16(const FactoryLease::Packet& p,unsigned o){return unsigned(p[o])*256+p[o+1];}
static unsigned u32(const FactoryLease::Packet& p,unsigned o){return (unsigned(p[o])<<24)|(unsigned(p[o+1])<<16)|(unsigned(p[o+2])<<8)|p[o+3];}
bool FactoryLease::valid(const Packet& p){return p.size()>=16&&p.size()<=65552&&u32(p,4)==p.size()-8&&p[12]==1&&p[13]==1;}
std::string FactoryLease::key(const Packet& p){std::string k; k.append((const char*)&p[0],4);k.append((const char*)&p[8],4);return k;}
bool FactoryLease::before(const Packet& p,unsigned role){
 if(!valid(p)||p[14]!=0||p[15]!=0||role>1){fault("invalid pre-send event");return false;}
 unsigned svc=u16(p,0),method=u16(p,2);unsigned lane=svc==0xb006?0:svc==0xb00e?1:2;
 if(lane>1||lane!=role||u16(p,8)==0x5348){fault("uncovered factory service or role");return false;}
 if(pending_.size()>=128||pending_.count(key(p))){fault("pending request collision/limit");return false;}
 unsigned handle=lane?100:200;
 if(method!=1&&(p.size()<20||u32(p,16)!=handle)){fault("factory instance mismatch");return false;}
 Pending entry;entry.packet=p;entry.lane=lane;++generation_;
 if(method==1||method==7){lanes_[lane].staged=Unknown;lanes_[lane].committed=Unknown;++lanes_[lane].generation;}
 // Pending requests revoke admission, but resource/child-model updates do not
 // fabricate a change to the explicitly tracked main visibility state.
 if(method==9){
  if(p.size()<25){fault("truncated model identity");return false;}
  bool mainModel=u32(p,20)==(lane?101U:0x21000000U);
  if(mainModel){
   lanes_[lane].staged=Unknown;lanes_[lane].committed=Active;++lanes_[lane].generation;
   if(lane==0&&p.size()==75&&p[24]==33&&u32(p,25)==42&&u32(p,29)==2&&u32(p,33)==0x21000000&&p[37]==33&&p[46]<=8)
    lanes_[lane].staged=p[46]==0?Idle:Active;
   if(lane==1&&p.size()==42&&p[24]==46&&u32(p,25)==9&&u32(p,29)==3&&u32(p,33)==101&&p[37]==46)
    lanes_[lane].staged=u32(p,38)==0xffffffff?Idle:Active;
  }
 }
 entry.generation=lanes_[lane].generation;
 if(method==4){if(p.size()!=20){fault("invalid commit body");return false;}entry.commit=lanes_[lane].staged;}
 pending_[key(p)]=entry;return true;
}
bool FactoryLease::outgoing(const Packet& p){
 if(!valid(p)){fault("invalid observed request");return false;}
 if(u16(p,8)==0x5348)return true;
 std::map<std::string,Pending>::iterator it=pending_.find(key(p));
 if(it==pending_.end()||it->second.packet!=p){fault("factory send without pre-send coverage");return false;}
 it->second.seen=true;return true;
}
bool FactoryLease::reply(const Packet& p){
 if(!valid(p)){fault("invalid factory reply");return false;}
 if(u16(p,8)==0x5348)return true;
 std::map<std::string,Pending>::iterator it=pending_.find(key(p));
 if(it==pending_.end()||!it->second.seen){fault("uncorrelated factory reply");return false;}
 if(p[14]!=128||p[15]!=0){fault("factory request failed");return false;}
 if(u16(p,2)==4){if(p.size()!=16){fault("invalid commit acknowledgement");return false;}if(lanes_[it->second.lane].generation==it->second.generation){lanes_[it->second.lane].committed=it->second.commit;if(it->second.commit==Idle)++idleCommits[it->second.lane];if(it->second.commit==Active)++activeCommits[it->second.lane];}}
 pending_.erase(it);++generation_;return true;
}
}
