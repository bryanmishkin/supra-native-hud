#include "native_backend.hpp"
#include <assert.h>
#include <stdio.h>
#include <limits>
using namespace supra;using namespace nbt::hudterm;
static NativeProfile profile() {
 NativeProfile p;p.mostHudConfirmed=p.geometryConfirmed=p.paletteConfirmed=p.ownershipConfirmed=true;
 p.host=0x101;p.image[0]=20;p.image[1]=21;p.width=480;p.height=240;p.maxItems=29;
 p.dimColour=1;p.tachColour=2;p.shiftColour=3;return p;
}
static Update frame() {
 Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;HudCore core(c);
 Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;in.rpm.valid=true;in.rpm.at=1000;in.rpm.value=6000;
 return core.update(in,1000);
}
int main() {
 Update u=frame();NativeBatch b;NativeBackend disabled((NativeProfile()));assert(!disabled.prepare(u,true,true,false,b)&&b.calls.empty());
 NativeProfile p=profile();NativeBackend backend(p);assert(backend.prepare(u,true,true,false,b));
 assert(b.calls.size()==40 && b.calls[0].fkt==kSetVisibility && b.calls[1].fkt==kRemoveAllItems);
 unsigned points=0;
 for(size_t i=0;i<b.calls.size();++i) {
  const Call& c=b.calls[i];assert(payloadShapeOk(c.fkt,c.payload));
  if(c.fkt==kAddPolygon) { ++points;assert(c.handle()==21);assert(c.payload.size()==14);
   for(size_t j=6;j<14;j+=4) { assert(rdBe16(&c.payload[j])<480);assert(rdBe16(&c.payload[j+2])<240); }
  }
 }
 assert(points==29);
 std::vector<NativeBatch> stages;assert(stageNativeBatch(b,32,stages));
 assert(stages.size()==2&&stages[0].calls.size()==32&&stages[1].calls.size()==8);
 assert(!stages[0].swap&&stages[1].swap&&stages[1].calls.back().fkt==kSwitchVisibility);
 assert(!stageNativeBatch(b,0,stages)&&stages.empty());
 assert(!stageNativeBatch(b,33,stages)&&stages.empty());const Call swap=b.calls.back();assert(swap.fkt==kSwitchVisibility);
 assert(swap.payload[0]==0&&swap.payload[1]==20&&swap.payload[2]==0&&swap.payload[3]==21);
 assert(!backend.prepare(u,true,true,false,b)&&b.calls.empty());backend.complete(true);
 assert(backend.prepare(u,true,true,false,b));assert(b.calls[1].handle()==20);backend.complete(false);
 assert(backend.failed()&&!backend.prepare(u,true,true,false,b));
 NativeBackend yielding(p);assert(yielding.prepare(u,true,true,false,b));assert(!yielding.prepare(u,true,true,true,b));
 yielding.complete(true);assert(yielding.failed());assert(!yielding.prepare(u,true,true,false,b));
 NativeBackend clearing(p);Update clear;clear.action=ClearOwned;assert(clearing.prepare(clear,true,true,false,b));assert(b.calls.size()==2);
 assert(b.calls[0].handle()==20&&b.calls[1].handle()==21&&b.calls[0].payload[2]==0&&b.calls[1].payload[2]==0);
 NativeBackend malformed(p);u.frame.tach[0].x1=std::numeric_limits<double>::quiet_NaN();assert(!malformed.prepare(u,true,true,false,b)&&b.calls.empty());
 p.image[1]=p.image[0];NativeBackend alias(p);assert(!alias.prepare(frame(),true,true,false,b));
 p=profile();p.maxItems=28;NativeBackend small(p);assert(!small.prepare(frame(),true,true,false,b));
 p=profile();p.geometryConfirmed=false;NativeBackend unknown(p);assert(!unknown.prepare(frame(),true,true,false,b));
 puts("PASS: native command shape, big-endian swap, 29 bounded items, owned-only clear, double-buffer acknowledgement, failure latch, overlay invalidation and invalid profiles/coordinates");
}
