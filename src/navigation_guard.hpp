#ifndef SUPRA_NAVIGATION_GUARD_HPP
#define SUPRA_NAVIGATION_GUARD_HPP
#include <stddef.h>
namespace supra {
enum Traffic {IgnoreTraffic,OwnTraffic,FactoryTraffic,UnknownTraffic};
// Passive revocation only. No observation here grants permission or ownership.
Traffic classifyTraffic(const unsigned char*,size_t captured,size_t wire,unsigned ownIp,unsigned ownPort,unsigned clusterIp);
}
#endif
