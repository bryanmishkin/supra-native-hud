#include "factory_rpm.hpp"
#include <cassert>
#include <cstring>
int main(){
 nbt::most::View v;memset(&v,0,sizeof(v));unsigned char raw[]={0x0b,0xcc};v.varTag=2;v.src=0x5000;v.dst=0x205e;v.fblock=5;v.fkt=0xcd0;v.op=12;v.data=raw;v.len=2;
 supra::Sample s;assert(supra::decodeFactoryRpm(v,0x205e,100,s)&&s.valid&&s.value==755&&s.at==100);
 v.src=0x5001;assert(!supra::decodeFactoryRpm(v,0x205e,101,s)&&s.at==100);v.src=0x5000;
 v.dst=0x205f;assert(!supra::decodeFactoryRpm(v,0x205e,101,s));v.dst=0x205e;
 v.varVal=4;assert(!supra::decodeFactoryRpm(v,0x205e,101,s));v.varVal=0;
 v.op=15;assert(supra::decodeFactoryRpm(v,0x205e,101,s)&&!s.valid);v.op=12;
 v.len=1;assert(supra::decodeFactoryRpm(v,0x205e,102,s)&&!s.valid);v.len=2;
 raw[0]=raw[1]=255;assert(supra::decodeFactoryRpm(v,0x205e,103,s)&&!s.valid);
 raw[0]=raw[1]=0;assert(supra::decodeFactoryRpm(v,0x205e,104,s)&&s.valid&&s.value==0);
 raw[0]=0x65;raw[1]=0x90;assert(supra::decodeFactoryRpm(v,0x205e,105,s)&&s.valid&&s.value==6500);
}
