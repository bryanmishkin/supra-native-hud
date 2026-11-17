#ifndef SUPRA_FACTORY_STREAM_HPP
#define SUPRA_FACTORY_STREAM_HPP
#include "factory_lease.hpp"
#include <map>
namespace supra {
class FactoryStream {
 struct Flow {unsigned next;bool established,own,shared;FactoryLease::Packet bytes;Flow():next(0),established(false),own(false),shared(false){}};
 std::map<std::string,Flow> flows_;FactoryLease& lease_;
public:
 explicit FactoryStream(FactoryLease& l):lease_(l){}
 void registerOwn(unsigned address,unsigned port);
 void ethernet(const unsigned char*,unsigned captured,unsigned wire);
};
}
#endif
