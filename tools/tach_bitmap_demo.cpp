// Offline synthetic values only. Never reads a vehicle or installs software.
#include "hud_core.hpp"
#include "tach_bitmap.hpp"
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <cerrno>
int main(int argc,char** argv) {
    if(argc!=3){std::cerr<<"usage: tach-bitmap-demo RPM OUTPUT.bgra\n";return 2;}
    char* end=0;errno=0;double rpm=std::strtod(argv[1],&end);
    if(errno || !end || *end || end==argv[1] || !(rpm>=0 && rpm<=7000))return 2;
    supra::Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;
    supra::Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;
    in.rpm.valid=true;in.rpm.value=rpm;in.rpm.at=1000;
    supra::HudCore core(c);supra::Update u=core.update(in,1000);
    if(u.action!=supra::Present)return 3;
    std::vector<unsigned char> p=supra::tachBitmap(u.frame);
    std::ofstream out(argv[2],std::ios::binary);out.write((const char*)&p[0],p.size());out.close();
    if(!out)return 4;
    std::cout<<"Synthetic RPM "<<rpm<<"; 150x36 opaque BGRA. Demo scale only, not vehicle limits.\n";
    return 0;
}
