#include "factory_background.hpp"
extern "C" int supra_background(const unsigned char* p,unsigned n){return supra::backgroundFactoryRequest(p,n)?1:0;}
