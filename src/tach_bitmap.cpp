#include "tach_bitmap.hpp"
#include <cstdio>
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

namespace {
void colorRect(std::vector<unsigned char>& p,int x,int y,int w,int h,
               unsigned char r,unsigned char g,unsigned char b) {
    for(int yy=y;yy<y+h;++yy)for(int xx=x;xx<x+w;++xx) {
        if(xx<0||yy<0||xx>=(int)W||yy>=(int)H)continue;
        unsigned n=4*(yy*W+xx);p[n]=b;p[n+1]=g;p[n+2]=r;
    }
}
const char* glyph(char c) {
    if(c>='0'&&c<='9')return digits[c-'0'];
    switch(c) {
    case 'R':return "110101110101101";
    case 'P':return "110101110100100";
    case 'M':return "101111111101101";
    case 'S':return "111100111001111";
    case 'I':return "111010010010111";
    case '+':return "000010111010000";
    case '-':return "000000111000000";
    case '.':return "000000000000010";
    case ',':return "000000000010100";
    default:return "000000000000000";
    }
}
void textV2(std::vector<unsigned char>& p,const char* s,int center,int y,
            int sx,int sy,unsigned char value,bool italic) {
    unsigned len=0;while(s[len])++len;
    int width=len?int(len)*(3*sx+sx)-sx:0;
    int x=center-(width+(italic?2:0))/2;
    for(unsigned i=0;i<len;++i)for(int row=0;row<5;++row)for(int col=0;col<3;++col)
        if(glyph(s[i])[row*3+col]=='1')
            rect(p,x+int(i)*4*sx+col*sx+(italic?(4-row)/2:0),y+row*sy,sx,sy,value);
}
}
std::vector<unsigned char> tachBitmapV2(const Frame& f) {
    std::vector<unsigned char> p(W*H*4,0);
    for(unsigned i=3;i<p.size();i+=4)p[i]=255;
    if(!f.visible||!(f.rpm>=0&&f.rpm<=7700))return p;
    // Shallow arch: fit the reference's silhouette without claiming more pixels.
    for(unsigned i=0;i<24;++i) {
        int d=int(i)-12,y=d*d/28;
        unsigned char r=90,g=210,b=255;
        if(i>=18){r=255;g=i>=22?40:(i>=20?100:170);b=0;}
        if(!f.tach[i].lit){r/=7;g/=7;b/=7;}
        colorRect(p,3+6*i,y,5,5,r,g,b);
    }
    unsigned lights=f.shiftLights>5?5:f.shiftLights;
    for(unsigned i=0;i<5;++i) {
        bool on=i<lights;
        colorRect(p,40+14*i,11,11,3,on?255:28,
                  on?((lights==5||i>=3)?40:170):12,on?0:8);
    }
    char number[16];unsigned rpm=(unsigned)(f.rpm+0.5);
    if(rpm>=1000)std::snprintf(number,sizeof(number),"%u,%03u",rpm/1000,rpm%1000);
    else std::snprintf(number,sizeof(number),"%u",rpm);
    textV2(p,number,38,15,3,3,255,true);
    colorRect(p,78,17,1,18,75,75,75);
    // boostVisible must come from a freshness-validated source. The standalone
    // V1 worker never sets it; only the offline demo supplies synthetic values.
    bool boost=f.boostVisible&&f.boostPsi>=-30&&f.boostPsi<=60;
    if(boost)std::snprintf(number,sizeof(number),"%+.1f",f.boostPsi);
    else std::snprintf(number,sizeof(number),"--.-");
    textV2(p,number,115,18,2,2,boost?255:90,true);
    textV2(p,"RPM",38,31,1,1,150,false);
    textV2(p,"PSI",115,31,1,1,boost?150:70,false);
    return p;
}

}
