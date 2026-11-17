#include "boost_input.hpp"
#include <cassert>
#include <cmath>
int main(){
 using namespace supra;
 unsigned char abs[]={0x62,0x42,0x05,0x31,0xec},ambient[]={0x62,0x42,0x01,0x63,0xd3};
 BoostCandidate b;assert(pressureCandidate(b.absolute,0x4205,abs,5,1000,1020));assert(pressureCandidate(b.ambient,0x4201,ambient,5,1020,1040));
 assert(std::fabs(b.absolute.value-99.84375)<0.000001);assert(std::fabs(b.ambient.value-99.82421875)<0.000001);
 Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=c.boostValidated=true;
 Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;in.rpm.valid=true;in.rpm.at=1040;in.rpm.value=650;b.apply(in);
 HudCore core(c);Update u=core.update(in,1050);assert(u.frame.boostVisible&&u.frame.boostPsi>0&&u.frame.boostPsi<0.01);
 // Old, future, wrong-identifier, malformed and sentinel input never become boost.
 assert(!pressureCandidate(b.absolute,0x4205,ambient,5,1100,1110));
 assert(!pressureCandidate(b.absolute,0x4205,abs,4,1100,1110));
 assert(!pressureCandidate(b.absolute,0x4205,abs,5,1100,1201));
 assert(!pressureCandidate(b.absolute,0x4205,abs,5,900,910));
 assert(!pressureCandidate(b.absolute,0x4205,abs,5,1100,1099));
 abs[3]=abs[4]=255;assert(!pressureCandidate(b.absolute,0x4205,abs,5,1100,1110));
 abs[3]=abs[4]=0;assert(!pressureCandidate(b.absolute,0x4205,abs,5,1100,1110));
 in.rpm.at=1350;u=core.update(in,1350);assert(u.action==Present&&!u.frame.boostVisible);
 in.manifoldKpa.at=1300;in.ambientKpa.at=1450;in.rpm.at=1450;u=core.update(in,1450);assert(!u.frame.boostVisible);
 in.manifoldKpa.at=1551;in.ambientKpa.at=1550;in.rpm.at=1550;u=core.update(in,1550);assert(!u.frame.boostVisible);
 return 0;
}
