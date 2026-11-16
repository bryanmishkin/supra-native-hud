#include "hud_app.hpp"
#include <stdio.h>
#include <string.h>
using namespace supra;
int main(int argc,char** argv) {
 if(argc!=2 || strcmp(argv[1],"--simulate")){fputs("Offline simulator only. Use --simulate; no vehicle connection is implemented.\n",stderr);return 64;}
 Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;c.staleMs=2000; // synthetic slow-transport fixture only
 NativeProfile p;p.mostHudConfirmed=p.geometryConfirmed=p.paletteConfirmed=p.ownershipConfirmed=true;
 p.host=0x101;p.image[0]=20;p.image[1]=21;p.width=480;p.height=240;p.maxItems=29;
 HudApp app(c,p,0x2001,true);puts("{\"simulation\":true,\"profile\":\"synthetic fixture, 2000ms TTL; not a Supra profile\",\"calls\":[");
 for(unsigned i=0;i<40;++i){
  uint64_t now=1000+i*50;Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=in.rpm.valid=true;in.rpm.value=6000;in.rpm.at=now;
  nbt::most::Msg m;if(!app.poll(in,now,m))return 1;
  printf("%s{\"time_ms\":%u,\"function\":%u,\"tag\":%u,\"payload_hex\":\"",i?",\n":"",(unsigned)now,m.fkt,m.hdrTag);
  for(size_t j=0;j<m.data.size();++j)printf("%02x",m.data[j]);
  printf("\"}");
  nbt::most::View v={0,0,0,0,0,0,0,0,0,0,0,0,0};v.varTag=2;v.src=m.dst;v.dst=m.src;v.fblock=m.fblock;v.inst=m.inst;v.fkt=m.fkt;v.hdrTag=m.hdrTag;v.op=nbt::most::kOpResultAck;v.data=&m.data[0];v.len=m.data.size();
  app.receive(in,v,now+1);if(app.failed())return 2;
 }
 puts("\n]}");return 0;
}
