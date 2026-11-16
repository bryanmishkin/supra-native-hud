#ifndef SUPRA_RPM_INPUT_HPP
#define SUPRA_RPM_INPUT_HPP
#include "hud_core.hpp"
#include <stddef.h>
namespace supra {
// Exact DME 41 0C response. Timestamp is request start, same monotonic clock as core.
// Any invalid/reordered/late reply invalidates the sample; no last-value reuse.
bool applyRpmReply(Input& in,const unsigned char* reply,size_t size,uint64_t requested,uint64_t received);
}
#endif
