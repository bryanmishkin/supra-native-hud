#include "standalone_wire.hpp"
#include <fstream>
#include <iostream>
#include <cstring>
using namespace supra;
int main(int argc,char** argv){try{
 if(argc==3&&!strcmp(argv[1],"--profile")){Profile p=readProfile(argv[2]);std::cout<<p.setup.size()<<" "<<p.cleanup.size()<<"\n";return 0;}
 if(argc!=3)return 64;std::ifstream in(argv[1],std::ios::binary);Bytes raw;char c;while(in.get(c))raw.push_back((unsigned char)c);Bytes out=encodeRle(raw,true);std::ofstream f(argv[2],std::ios::binary);f.write((const char*)&out[0],out.size());if(!f)return 2;return 0;
 }catch(...){return 2;}}
