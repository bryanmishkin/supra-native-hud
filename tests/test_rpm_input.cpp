#include "rpm_input.hpp"
#include "tach_bitmap.hpp"
#include <cassert>
int main(){
 supra::Input in;unsigned char captured[]={0x41,0x0c,0x0f,0x6e};
 assert(supra::applyRpmReply(in,captured,4,1000,1020));assert(in.rpm.value==987.5);
 supra::Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;supra::HudCore core(c);
 assert(core.update(in,1020).action==supra::NoChange); // unknown navigation/ownership blocks drawing
 in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;
 supra::Update u=core.update(in,1020);assert(u.action==supra::Present);assert(supra::tachBitmap(u.frame).size()==21600);
 in.factoryOverlay=true;assert(core.update(in,1021).action==supra::ClearOwned);
 assert(!supra::applyRpmReply(in,captured,4,900,950));assert(!in.rpm.valid);assert(!supra::applyRpmReply(in,captured,4,800,850));
 assert(!supra::applyRpmReply(in,captured,4,1100,1401));
 unsigned char negative[]={0x7f,0x01,0x11};assert(!supra::applyRpmReply(in,negative,3,1500,1510));
 captured[2]=0x0a;captured[3]=0x44;assert(supra::applyRpmReply(in,captured,4,1600,1610));assert(in.rpm.value==657);
 in.factoryOverlay=false;assert(core.update(in,1901).action==supra::NoChange);
}
