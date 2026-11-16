#include "tach_bitmap.hpp"
#include <cassert>
#include <limits>
int main(){
 supra::Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;
 supra::HudCore core(c);supra::Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;
 in.rpm.valid=true;in.rpm.at=100;in.rpm.value=3500;
 supra::Update u=core.update(in,100);assert(u.action==supra::Present);
 std::vector<unsigned char> p=supra::tachBitmap(u.frame);assert(p.size()==21600);
 for(unsigned i=3;i<p.size();i+=4)assert(p[i]==255);
 assert(p[4*(3*150+3)]==255);assert(p[4*(3*150+3+6*12)]==40);
 in.factoryOverlay=true;assert(core.update(in,101).action==supra::ClearOwned);
 supra::Frame blank; p=supra::tachBitmap(blank);
 for(unsigned i=0;i<p.size();++i)assert(p[i]==(i%4==3?255:0));
 blank.visible=true;blank.rpm=std::numeric_limits<double>::quiet_NaN();p=supra::tachBitmap(blank);
 for(unsigned i=0;i<p.size();++i)assert(p[i]==(i%4==3?255:0));
 in.factoryOverlay=false;in.overlayStateKnown=false;assert(core.update(in,102).action==supra::NoChange);
 return 0;
}
