#ifndef SUPRA_FACTORY_RPM_HPP
#define SUPRA_FACTORY_RPM_HPP
#include "hud_core.hpp"
#include "most/ids.hpp"
#include "most/msg.hpp"
namespace supra {
// Reference-car EngineSpeed2: unsigned big-endian quarter RPM, not a CAN ID.
inline bool decodeFactoryRpm(const nbt::most::View& m,unsigned self,uint64_t at,Sample& out){
 if(nbt::most::classify(m)!=nbt::most::kNormal||m.src!=0x5000||m.dst!=self||m.fblock!=5||m.inst||m.fkt!=0xcd0)return false;
 out.valid=false;
 if(m.op!=nbt::most::kOpStatus||m.len!=2||!m.data)return true;
 unsigned raw=(unsigned(m.data[0])<<8)|m.data[1];
 if(raw>30800)return true;
 out.value=raw/4.0;out.at=at;out.valid=true;return true;
}
bool startFactoryRpm();
Sample latestFactoryRpm();
}
#endif
