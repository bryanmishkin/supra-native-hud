#include "navigation_guard.hpp"
#include <cassert>
#include <vector>
using namespace supra;
int main(){
 std::vector<unsigned char> p(55,0);p[12]=8;p[14]=0x45;p[16]=0;p[17]=41;p[23]=6;
 p[26]=127;p[29]=1;p[30]=160;p[31]=48;p[32]=199;p[33]=96;
 p[34]=0x12;p[35]=0x34;p[36]=0x77;p[37]=0x26;p[46]=0x50;
 assert(classifyTraffic(&p[0],55,55,0x7f000001,0x1234,0xa030c760)==OwnTraffic);
 assert(classifyTraffic(&p[0],55,55,0x7f000002,0x1234,0xa030c760)==FactoryTraffic);
 assert(classifyTraffic(&p[0],55,55,0x7f000001,0x1235,0xa030c760)==FactoryTraffic);
 for(unsigned n=0;n<55;++n)assert(classifyTraffic(&p[0],n,55,0,0,0xa030c760)==UnknownTraffic);
 p[20]=0x20;assert(classifyTraffic(&p[0],55,55,0,0,0xa030c760)==UnknownTraffic);p[20]=0;
 p[17]=40;assert(classifyTraffic(&p[0],55,55,0,0,0xa030c760)==IgnoreTraffic);p[17]=41;
 p.insert(p.begin()+12,4,0);p[12]=0x81;p[13]=0;
 assert(classifyTraffic(&p[0],59,59,0,0,0xa030c760)==FactoryTraffic);
 p.erase(p.begin()+12,p.begin()+16);p[12]=8;p[13]=0;
 const unsigned char cookie[]={255,255,0,0,0,0,0,8,222,173,190,239,1,1,1,0};
 p.resize(54);p.insert(p.end(),cookie,cookie+16);p[17]=56;
 assert(classifyTraffic(&p[0],70,70,0,0,0xa030c760)==IgnoreTraffic);
 p[69]=1;assert(classifyTraffic(&p[0],70,70,0,0,0xa030c760)==FactoryTraffic);
 return 0;
}
