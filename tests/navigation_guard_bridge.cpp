#include "navigation_guard.hpp"
extern "C" int classify(const unsigned char* p,size_t n,size_t wire,unsigned ip,unsigned port,unsigned cluster){return supra::classifyTraffic(p,n,wire,ip,port,cluster);}
