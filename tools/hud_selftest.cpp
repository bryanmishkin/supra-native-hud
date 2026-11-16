// No vehicle I/O, DSI loading, files, sockets or drawing. All messages stay in memory.
#include "hud_app.hpp"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <unistd.h>
using namespace supra;
static Config config(){Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;return c;}
static NativeProfile profile(){NativeProfile p;p.mostHudConfirmed=p.geometryConfirmed=p.paletteConfirmed=p.ownershipConfirmed=true;p.host=0x101;p.image[0]=20;p.image[1]=21;p.width=480;p.height=240;p.maxItems=29;return p;}
static Input input(uint64_t t,double rpm=6000){Input i;i.connected=i.ownershipConfirmed=i.overlayStateKnown=i.rpm.valid=true;i.rpm.at=t;i.rpm.value=rpm;return i;}
static nbt::most::View ack(const nbt::most::Msg& m){nbt::most::View v={0,2,0,0,0,0,0,0,0,0,0,0,0};v.src=m.dst;v.dst=m.src;v.fblock=m.fblock;v.inst=m.inst;v.fkt=m.fkt;v.hdrTag=m.hdrTag;v.op=nbt::most::kOpResultAck;v.data=&m.data[0];v.len=m.data.size();return v;}
static bool defaults(){HudApp a(Config(),NativeProfile(),0,false);nbt::most::Msg m;return !a.poll(Input(),1000,m);}
static bool sweep(){for(int rpm=-1;rpm<=7800;++rpm){HudCore h(config());Update u=h.update(input(1000,rpm),1000);if(rpm<0||rpm>7700){if(u.action!=NoChange)return false;}else if(u.action!=Present||u.frame.shiftLights>5)return false;}return true;}
static bool rollback(){HudCore h(config());h.update(input(1000),1000);h.update(input(1000),1090);return h.update(input(1000),1050).action==ClearOwned;}
static bool ordering(){HudCore h(config());h.update(input(1000),1000);h.update(input(1050),1050);return h.update(input(1020),1100).action==ClearOwned;}
static bool pipeline(){Config c=config();c.staleMs=2000;HudApp a(c,profile(),0x2001,true);nbt::most::Msg m;unsigned swaps=0;for(unsigned i=0;i<40;++i){uint64_t now=1000+i*50;if(!a.poll(input(now),now,m))return false;if(m.fkt==nbt::hudterm::kSwitchVisibility){++swaps;if(i!=39)return false;}a.receive(input(now),ack(m),now+1);if(a.failed())return false;}a.receive(input(3100),ack(m),3100);return swaps==1&&a.poll(input(3100),3100,m);}
static bool stale(){HudApp a(config(),profile(),0x2001,true);nbt::most::Msg m;Input in=input(1000);if(!a.poll(in,1000,m))return false;return !a.poll(in,1301,m)&&a.failed();}
static bool frameExpiry(){HudApp a(config(),profile(),0x2001,true);nbt::most::Msg m;if(!a.poll(input(1000),1000,m))return false;a.receive(input(1001),ack(m),1001);return !a.poll(input(1301),1301,m)&&a.failed();}
static bool overlay(){HudApp a(config(),profile(),0x2001,true);nbt::most::Msg m;Input in=input(1000);if(!a.poll(in,1000,m))return false;in.factoryOverlay=true;a.receive(in,ack(m),1001);return a.failed()&&!a.poll(input(1002),1002,m);}
static bool timeout(){NativeSession s(profile(),0x2001,true);Config c=config();c.staleMs=2000;HudCore h(c);nbt::most::Msg m;if(!s.submit(h.update(input(1000),1000),1000,true)||!s.next(1000,true,m))return false;s.tick(2500,true);return s.failed();}
static bool clockWorks(){timespec a,b;return clock_gettime(CLOCK_MONOTONIC,&a)==0&&clock_gettime(CLOCK_MONOTONIC,&b)==0&&(b.tv_sec>a.tv_sec||(b.tv_sec==a.tv_sec&&b.tv_nsec>=a.tv_nsec));}
static void deadline(int){_exit(124);}
int main(int argc,char** argv){
 if(argc!=2||strcmp(argv[1],"--self-test")){fputs("Usage: supra-hud-selftest-qnx --self-test (no vehicle I/O)\n",stderr);return 64;}
 signal(SIGALRM,deadline);alarm(5);
 struct Case {const char* name;bool (*run)();} cases[]={
  {"default_suppression",defaults},{"rpm_sweep",sweep},{"clock_rollback",rollback},
  {"sample_order",ordering},{"pipeline_and_reply_cadence",pipeline},{"stale_input",stale},
  {"frame_expiry_despite_fresh_input",frameExpiry},{"overlay_revocation",overlay},{"ack_timeout",timeout},{"monotonic_clock",clockWorks}};
#ifdef __QNXNTO__
 const bool target=true;
#else
 const bool target=false;
#endif
 bool all=true;printf("{\"schema\":1,\"qnx_target\":%s,\"pointer_bits\":%u,\"vehicle_io\":false,\"tests\":[",target?"true":"false",(unsigned)(sizeof(void*)*8));
 for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i){bool ok=cases[i].run();all=all&&ok;printf("%s{\"name\":\"%s\",\"pass\":%s}",i?",":"",cases[i].name,ok?"true":"false");}
 printf("],\"pass\":%s}\n",all?"true":"false");fflush(stdout);return all?0:1;
}
