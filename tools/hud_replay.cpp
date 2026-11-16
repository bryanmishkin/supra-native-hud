#include "hud_core.hpp"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
using namespace supra;
// Offline-only, explicit simulator. Thresholds are demonstration values, not vehicle calibration.
int main(int argc,char** argv) {
 if(argc!=2 || strcmp(argv[1],"--demo-svg")) { fputs("Usage: hud-replay --demo-svg (simulation only)\n",stderr);return 64; }
 Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;
 HudCore core(c);Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;
 in.rpm.valid=true;in.rpm.at=1000;in.rpm.value=6000;
 Update u=core.update(in,1000);if(u.action!=Present)return 1;
 puts("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 360' role='img' aria-label='Supra HUD offline geometry study'>");
 puts("<rect width='1000' height='360' fill='#080a0c'/><text x='60' y='35' fill='#bbb' font-family='sans-serif' font-size='16'>SIMULATION • normalized geometry • demonstration thresholds</text>");
 for(unsigned i=0;i<24;++i) { const Segment& s=u.frame.tach[i];printf("<line x1='%g' y1='%g' x2='%g' y2='%g' stroke='%s' stroke-width='13'/>\n",s.x1*1000,40+s.y1*600,s.x2*1000,40+s.y2*600,s.lit?"#eeeeee":"#333333"); }
 for(unsigned i=0;i<5;++i)printf("<circle cx='%u' cy='175' r='8' fill='%s'/>\n",420+i*40,i<u.frame.shiftLights?"#e52c35":"#333333");
 printf("<text x='500' y='230' text-anchor='middle' fill='white' font-family='sans-serif' font-size='30'>%.0f RPM</text>\n",u.frame.rpm);
 puts("<text x='500' y='285' text-anchor='middle' fill='#888' font-family='sans-serif' font-size='18'>Factory speed / speed-limit region reserved</text><text x='500' y='325' text-anchor='middle' fill='#888' font-family='sans-serif' font-size='14'>Native scale, placement and overlay ownership await car validation</text></svg>");
 return 0;
}
