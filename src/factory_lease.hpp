#ifndef SUPRA_FACTORY_LEASE_HPP
#define SUPRA_FACTORY_LEASE_HPP
#include <map>
#include <vector>
#include <string>
namespace supra {
// This state is RAM-only. Unknown boot/reconnect state never grants drawing.
class FactoryLease {
public:
 typedef std::vector<unsigned char> Packet;
 enum Visibility {Unknown,Idle,Active};
 struct Lane {Visibility staged,committed;unsigned generation;Lane():staged(Unknown),committed(Unknown),generation(0){}};
 struct Pending {Packet packet;unsigned lane,generation;Visibility commit;bool seen;Pending():lane(0),generation(0),commit(Unknown),seen(false){}};
 FactoryLease():fault_(false),generation_(0){for(unsigned i=0;i<2;++i)idleCommits[i]=activeCommits[i]=0;}
 unsigned idleCommits[2],activeCommits[2];
 bool before(const Packet&,unsigned role);
 bool outgoing(const Packet&);
 bool reply(const Packet&);
 bool available() const {return !fault_&&pending_.empty()&&lanes_[0].committed==Idle&&lanes_[1].committed==Idle;}
 void fault(const char* why){fault_=true;reason_=why;++generation_;}
 bool failed()const{return fault_;}const std::string& reason()const{return reason_;}
 unsigned generation()const{return generation_;}
 Visibility state(unsigned lane)const{return lane<2?lanes_[lane].committed:Unknown;}
 static bool valid(const Packet&);
private:
 Lane lanes_[2];std::map<std::string,Pending> pending_;bool fault_;unsigned generation_;std::string reason_;
 static std::string key(const Packet&);
};
}
#endif
