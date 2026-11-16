#include "native_session.hpp"
#include <assert.h>
#include <stdio.h>
using namespace supra;
static NativeProfile profile() {
 NativeProfile p;p.mostHudConfirmed=p.geometryConfirmed=p.paletteConfirmed=p.ownershipConfirmed=true;
 p.host=0x101;p.image[0]=20;p.image[1]=21;p.width=480;p.height=240;p.maxItems=29;return p;
}
static Update frame(uint64_t at=1000) {
 Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;c.staleMs=2000;HudCore core(c);Input i;
 i.connected=i.ownershipConfirmed=i.overlayStateKnown=i.rpm.valid=true;i.rpm.value=6000;i.rpm.at=at;return core.update(i,at);
}
static nbt::most::View ack(const nbt::most::Msg& m) {
 nbt::most::View v={};v.txType=0;v.varTag=2;v.varVal=0;v.src=m.dst;v.dst=m.src;
 v.fblock=m.fblock;v.inst=m.inst;v.fkt=m.fkt;v.hdrTag=m.hdrTag;v.op=nbt::most::kOpResultAck;
 v.data=&m.data[0];v.len=m.data.size();return v;
}
int main() {
 NativeProfile p=profile();Update u=frame();nbt::most::Msg m;
 NativeSession unverified(p,0x2001,false);assert(!unverified.submit(u,1000,true));
 NativeSession s(p,0x2001,true);assert(s.submit(u,1000,true));
 unsigned swaps=0;uint64_t now=1000;uint32_t oldTag=0;
 for(unsigned i=0;i<40;++i) {
  assert(s.next(now,true,m));assert(m.hdrTag>oldTag);oldTag=m.hdrTag;
  if(m.fkt==nbt::hudterm::kSwitchVisibility){++swaps;assert(i==39);}
  nbt::most::Msg unused;assert(!s.next(now,true,unused));
  nbt::most::View v=ack(m);v.hdrTag++;s.receive(v,now+1,true);assert(s.busy());
  v=ack(m);v.src++;s.receive(v,now+2,true);assert(s.busy());
  v=ack(m);s.receive(v,now+3,true);assert(!s.failed());
  assert(!s.next(now+4,true,unused));now+=50;
 }
 assert(swaps==1&&!s.busy());assert(s.submit(frame(now),now,true));assert(s.next(now,true,m));
 s.tick(now+1500,true);assert(s.failed());s.receive(ack(m),now+1501,true);assert(!s.busy());
 NativeSession revoke(p,0x2001,true);assert(revoke.submit(frame(10),10,true));assert(revoke.next(10,true,m));
 revoke.tick(11,false);assert(revoke.failed());assert(!revoke.next(12,true,m));
 NativeSession rollback(p,0x2001,true);assert(rollback.submit(frame(100),100,true));rollback.tick(99,true);assert(rollback.failed());
 NativeSession error(p,0x2001,true);assert(error.submit(frame(1),1,true));assert(error.next(1,true,m));
 nbt::most::View v=ack(m);v.op=nbt::most::kOpError;error.receive(v,2,true);assert(error.failed());
 NativeSession writeFailure(p,0x2001,true);assert(writeFailure.submit(frame(1),1,true));writeFailure.sendFailed();assert(writeFailure.failed());
 puts("PASS: native sequencing, one in flight, 50ms spacing, exact acknowledgement correlation, final swap, timeout, permission revocation, late replies, rollback and send failure");
}
