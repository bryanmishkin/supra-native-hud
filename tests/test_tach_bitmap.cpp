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
 supra::Frame sport; sport.visible=true;sport.rpm=6500;sport.shiftLights=5;
 for(unsigned i=0;i<24;++i)sport.tach[i].lit=true;
 p=supra::tachBitmapSport(sport);assert(p.size()==21600);
 for(unsigned i=3;i<p.size();i+=4)assert(p[i]==255);
 unsigned orange=4*(0*150+3+6*18), red=4*(0*150+3+6*22);
 assert(p[orange]==0 && p[orange+1]==150 && p[orange+2]==255);
 assert(p[red]==0 && p[red+1]==40 && p[red+2]==255);
 assert(p[4*(19*150+82)+1]==40);
 sport.visible=false;p=supra::tachBitmapSport(sport);
 for(unsigned i=0;i<p.size();++i)assert(p[i]==(i%4==3?255:0));
 // V2 stays inside the known opaque canvas, including invalid-input clearing.
 p=supra::tachBitmapV2(sport);
 for(unsigned i=0;i<p.size();++i)assert(p[i]==(i%4==3?255:0));
 sport.visible=true;sport.rpm=4250;sport.boostVisible=false;
 std::vector<unsigned char> missing=supra::tachBitmapV2(sport);
 assert(missing.size()==21600);
 for(unsigned i=3;i<missing.size();i+=4)assert(missing[i]==255);
 unsigned cyan=4*(7*150+4);
 assert(missing[cyan]==255&&missing[cyan+1]==210&&missing[cyan+2]==90);
 bool shaded=false,bottom=false;
 for(unsigned y=21;y<35;++y)for(unsigned x=3;x<74;++x) {
  unsigned v=missing[4*(y*150+x)];
  if(v>0&&v<255)shaded=true;
  if(y==34&&v>0)bottom=true;
 }
 assert(shaded&&bottom); // native edge coverage and 14px digit height
 sport.boostVisible=true;sport.boostPsi=12.4;p=supra::tachBitmapV2(sport);
 assert(p!=missing);
 // Boost changes only the right readout, never RPM, arc or shift indication.
 for(unsigned y=0;y<36;++y)for(unsigned x=0;x<150;++x)
  if(y<18||x<80)for(unsigned k=0;k<4;++k)
   assert(p[4*(y*150+x)+k]==missing[4*(y*150+x)+k]);
 sport.boostPsi=std::numeric_limits<double>::quiet_NaN();
 assert(supra::tachBitmapV2(sport)==missing);
 sport.boostPsi=61;assert(supra::tachBitmapV2(sport)==missing);
 sport.boostPsi=-31;assert(supra::tachBitmapV2(sport)==missing);
 sport.rpm=7701;p=supra::tachBitmapV2(sport);
 for(unsigned i=0;i<p.size();++i)assert(p[i]==(i%4==3?255:0));
 sport.rpm=std::numeric_limits<double>::quiet_NaN();p=supra::tachBitmapV2(sport);
 for(unsigned i=0;i<p.size();++i)assert(p[i]==(i%4==3?255:0));
 return 0;
}
