#include "hud_app.hpp"
#include <assert.h>
#include <stdio.h>
using namespace supra;
static NativeProfile profile(){NativeProfile p;p.mostHudConfirmed=p.geometryConfirmed=p.paletteConfirmed=p.ownershipConfirmed=true;p.host=0x101;p.image[0]=20;p.image[1]=21;p.width=480;p.height=240;p.maxItems=29;return p;}
static Input input(uint64_t now){Input i;i.connected=i.ownershipConfirmed=i.overlayStateKnown=i.rpm.valid=true;i.rpm.value=6000;i.rpm.at=now;return i;}
static nbt::most::View ack(const nbt::most::Msg& m){nbt::most::View v={};v.varTag=2;v.src=m.dst;v.dst=m.src;v.fblock=m.fblock;v.inst=m.inst;v.fkt=m.fkt;v.hdrTag=m.hdrTag;v.op=nbt::most::kOpResultAck;v.data=&m.data[0];v.len=m.data.size();return v;}
int main(){
 Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;NativeProfile p=profile();nbt::most::Msg m;
 HudApp defaults(Config(),NativeProfile(),0,false);assert(!defaults.poll(Input(),0,m));
 Config simulated=c;simulated.staleMs=2000;
 HudApp app(simulated,p,0x2001,true);unsigned swaps=0;
 for(unsigned i=0;i<40;++i){uint64_t now=1000+i*50;Input in=input(now);assert(app.poll(in,now,m));if(m.fkt==nbt::hudterm::kSwitchVisibility)++swaps;app.receive(in,ack(m),now+1);assert(!app.failed());}
 assert(swaps==1);
 // A late reply while idle must not consume the next frame's presentation slot.
 app.receive(input(3100),ack(m),3100);
 assert(app.poll(input(3100),3100,m));

 HudApp expired(c,p,0x2001,true);assert(expired.poll(input(1000),1000,m));
 expired.receive(input(1001),ack(m),1001);
 assert(!expired.poll(input(1301),1301,m)&&expired.failed()); // fresh input cannot revive queued frame
 HudApp stale(c,p,0x2001,true);Input old=input(1000);assert(stale.poll(old,1000,m));assert(!stale.poll(old,1301,m));assert(stale.failed());
 HudApp revoke(c,p,0x2001,true);Input in=input(1000);assert(revoke.poll(in,1000,m));in.factoryOverlay=true;revoke.receive(in,ack(m),1001);assert(revoke.failed());assert(!revoke.poll(input(1002),1002,m));
 HudApp stopped(c,p,0x2001,true);stopped.stop();assert(!stopped.poll(input(1000),1000,m));
 puts("PASS: integrated HUD core-to-native replay, default-disabled behavior, stale input cancellation, overlay revocation and stop");
}
