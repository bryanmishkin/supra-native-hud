#include "hud_core.hpp"
#include <assert.h>
#include <limits>
#include <stdio.h>
using namespace supra;
static Sample sample(double value,uint64_t at) { Sample s;s.value=value;s.at=at;s.valid=true;return s; }
int main() {
 Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;
 Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;in.rpm=sample(6000,1000);
 HudCore defaults((Config()));assert(defaults.update(in,1000).action==NoChange);
 HudCore h(c);Update u=h.update(in,1000);assert(u.action==Present&&u.frame.shiftLights==3);
 for(unsigned i=0;i<24;++i)assert(u.frame.tach[i].x1>=0&&u.frame.tach[i].x2<=1&&u.frame.tach[i].y1>=0&&u.frame.tach[i].y1<=1);
 assert(h.update(in,1050).action==NoChange);
 in.factoryOverlay=true;assert(h.update(in,1051).action==ClearOwned);assert(h.update(in,1052).action==NoChange);
 in.factoryOverlay=false;assert(h.update(in,1053).action==Present);
 assert(h.update(in,1301).action==ClearOwned); // stale, despite cadence
 in.rpm=sample(6500,1400);u=h.update(in,1400);assert(u.frame.shiftLights==5);
 assert(h.update(in,1399).action==ClearOwned); // rollback
 in.rpm=sample(std::numeric_limits<double>::quiet_NaN(),1500);assert(h.update(in,1500).action==NoChange);
 in.rpm=sample(1000,2000);assert(h.update(in,1900).action==NoChange); // future sample
 in.rpm=sample(1000,2000);in.ownershipConfirmed=false;assert(h.update(in,2000).action==NoChange);
 in.ownershipConfirmed=true;in.overlayStateKnown=false;assert(h.update(in,2000).action==NoChange);
 in.overlayStateKnown=true;in.manifoldKpa=sample(200,2000);in.ambientKpa=sample(100,2000);
 assert(!h.update(in,2000).frame.boostVisible);
 c.boostValidated=true;HudCore b(c);u=b.update(in,2000);assert(u.frame.boostVisible&&u.frame.boostPsi>14.50&&u.frame.boostPsi<14.51);
 in.manifoldKpa=sample(200,2200);in.ambientKpa=sample(100,2000);assert(!b.update(in,2200).frame.boostVisible);
 in.connected=false;assert(b.update(in,2201).action==ClearOwned);
 in.connected=true;c.shiftRpm=8000;HudCore bad(c);assert(bad.update(in,2201).action==NoChange);
 c.shiftRpm=6500;
 for(int rpm=-1;rpm<=7800;++rpm) {
   HudCore sweep(c);in.rpm=sample(rpm,3000);Update frame=sweep.update(in,3000);
   if(rpm<0 || rpm>7700) assert(frame.action==NoChange);
   else { assert(frame.action==Present);assert(frame.frame.shiftLights<=5); }
 }
 HudCore between(c);in.rpm=sample(1000,4000);assert(between.update(in,4000).action==Present);
 assert(between.update(in,4090).action==NoChange);
 assert(between.update(in,4050).action==ClearOwned); // rollback inside one frame interval
 HudCore order(c);in.rpm=sample(1000,5000);assert(order.update(in,5000).action==Present);
 in.rpm=sample(2000,5050);assert(order.update(in,5050).action==NoChange);
 in.rpm=sample(3000,5020);assert(order.update(in,5100).action==ClearOwned); // fresh but out of order
 HudCore replies(c);in.rpm=sample(1000,6000);assert(replies.update(in,6000).action==Present);
 in.rpm=sample(2000,6050);assert(replies.observe(in,6050));
 in.rpm=sample(2000,6020);assert(replies.update(in,6100).action==ClearOwned);
 puts("PASS: HUD defaults, geometry bounds, cadence, immediate yield, staleness, clock rollback, invalid/future data, ownership, optional boost and skew");
}
