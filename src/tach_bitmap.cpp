#include "tach_bitmap.hpp"
namespace supra {
namespace {
const unsigned W=150,H=36;
void pixel(std::vector<unsigned char>& p,int x,int y,unsigned char v) {
    if(x<0 || y<0 || x>=(int)W || y>=(int)H)return;
    unsigned n=4*(y*W+x);p[n]=p[n+1]=p[n+2]=v;
}
void rect(std::vector<unsigned char>& p,int x,int y,int w,int h,unsigned char v) {
    for(int j=y;j<y+h;++j)for(int i=x;i<x+w;++i)pixel(p,i,j,v);
}
const char* digits[]={"111101101101111","010110010010111","111001111100111",
 "111001111001111","101101111001001","111100111001111","111100111101111",
 "111001001001001","111101111101111","111101111001111"};
}
std::vector<unsigned char> tachBitmap(const Frame& f) {
    std::vector<unsigned char> p(W*H*4,0);
    for(unsigned i=3;i<p.size();i+=4)p[i]=255;
    if(!f.visible || !(f.rpm>=0 && f.rpm<=22000))return p;
    // The existing core owns thresholds, freshness, cadence and segment state.
    for(unsigned i=0;i<24;++i)rect(p,3+6*i,3,4,8,f.tach[i].lit?255:40);
    unsigned n=(unsigned)(f.rpm+0.5); unsigned d[5];
    for(int i=4;i>=0;--i){d[i]=n%10;n/=10;}
    bool started=false;
    for(unsigned i=0;i<5;++i){
        if(d[i] || i==4)started=true;
        if(!started)continue;
        for(unsigned y=0;y<5;++y)for(unsigned x=0;x<3;++x)
            if(digits[d[i]][y*3+x]=='1')rect(p,4+8*i+2*x,17+2*y,2,2,255);
    }
    for(unsigned i=0;i<5;++i)rect(p,83+12*i,19,8,6,i<f.shiftLights?255:40);
    return p;
}
std::vector<unsigned char> tachBitmapSport(const Frame& f) {
    std::vector<unsigned char> p(W*H*4,0);
    for(unsigned i=3;i<p.size();i+=4)p[i]=255;
    if(!f.visible || !(f.rpm>=0 && f.rpm<=22000))return p;
    // Rising shoulder followed by a level sweep, within negotiated 150x36.
    for(unsigned i=0;i<24;++i) {
        int y=i<6?6-(int)i:0;
        rect(p,3+6*i,y,5,8,f.tach[i].lit?255:24);
        if(f.tach[i].lit && i>=18) {
            for(int yy=y;yy<y+8;++yy)for(int xx=3+6*i;xx<8+6*(int)i;++xx) {
                unsigned n=4*(yy*W+xx);p[n]=0;p[n+1]=i>=22?40:150;p[n+2]=255;
            }
        }
    }
    unsigned n=(unsigned)(f.rpm+0.5), d[5];
    for(int i=4;i>=0;--i){d[i]=n%10;n/=10;}
    bool started=false;
    for(unsigned i=0;i<5;++i){
        if(d[i] || i==4)started=true;
        if(!started)continue;
        for(unsigned y=0;y<5;++y)for(unsigned x=0;x<3;++x)
            if(digits[d[i]][y*3+x]=='1')rect(p,2+15*i+4*x,15+4*y,4,4,255);
    }
    // Five steady progressive shift lights; no time-based flashing.
    for(unsigned i=0;i<5;++i) {
        bool lit=i<f.shiftLights;
        for(int y=19;y<32;++y)for(int x=82+14*i;x<93+14*(int)i;++x){
            unsigned n=4*(y*W+x);p[n]=lit?0:24;
            p[n+1]=lit?((f.shiftLights>=5 || i>=3)?40:150):24;
            p[n+2]=lit?255:24;
        }
    }
    return p;
}

}
