#include "standalone_wire.hpp"
#include <fstream>
#include <stdexcept>
namespace supra {
static void require(bool ok){if(!ok)throw std::runtime_error("Invalid bounded wire/profile data");}
unsigned read32(const Bytes& b,unsigned p){require(p<=b.size() && b.size()-p>=4);return (unsigned(b[p])<<24)|(unsigned(b[p+1])<<16)|(unsigned(b[p+2])<<8)|b[p+3];}
void put32(Bytes& b,unsigned v){for(int i=3;i>=0;--i)b.push_back((v>>(i*8))&255);}
void set32(Bytes& b,unsigned p,unsigned v){require(p<=b.size() && b.size()-p>=4);for(int i=3;i>=0;--i)b[p+3-i]=(v>>(i*8))&255;}
static void put16(Bytes& b,unsigned v){b.push_back((v>>8)&255);b.push_back(v&255);}
Profile readProfile(const char* path){
 std::ifstream f(path,std::ios::binary);Bytes b;char c;while(f.get(c)){require(b.size()<8192);b.push_back((unsigned char)c);}require(f.eof() && b.size()>=8);
 require(b[0]=='S'&&b[1]=='H'&&b[2]=='P'&&b[3]=='1'&&b[4]==0&&b[5]==10&&b[6]==0&&b[7]==7);
 const unsigned methods[]={9,10,10,11,14,10,12,4,9,9,9,9,12,11,4,14,9};
 const unsigned types[]={33,34,29,10,40,15,32,0,33,17,33,33,32,10,0,40,17};
 const unsigned ids[]={0x21000000,0x22000004,0x1d00001d,0x0a000004,0x27000004,0x0f000004,0x20000000,0,0x21000000,0x11000000,0x21000000,0x21000000,0x20000000,0x0a000004,0,0x27000004,0x11000000};
 Profile p;unsigned at=8;
 for(unsigned i=0;i<17;++i){require(b.size()-at>=6);unsigned m=(b[at]<<8)|b[at+1],n=read32(b,at+2);at+=6;require(m==methods[i]&&n>=4&&n<=128&&n<=b.size()-at);Command row;row.method=m;row.body=Bytes(b.begin()+at,b.begin()+at+n);at+=n;require(read32(row.body,0)==200);
  if(types[i])require(n>=17 && row.body[8]==types[i] && read32(row.body,4)==ids[i] && read32(row.body,9)==n-17);else require(n==4);
  if(i==3)require(n==17&&read32(row.body,9)==0&&read32(row.body,13)==0);
  if(i==5)require(n==62&&row.body[33]==0);
  if(i==8||i==10||i==11)require(n==59&&row.body[30]==(i==8?2:(i==10?5:0)));
  if(i==4)require(n==38&&read32(row.body,32)==0x01000009);
  if(i<10)p.setup.push_back(row);else p.cleanup.push_back(row);
 }
 require(at==b.size());return p;
}
Bytes encodeRle(const Bytes& raw,bool swap){
 require(raw.size()==21600);Bytes pixels(raw),out,literal;
 for(unsigned i=0;i<pixels.size();i+=4){require(pixels[i+3]==255);unsigned char a=pixels[i],b=pixels[i+1],c=pixels[i+2];pixels[i]=255;pixels[i+1]=swap?a:c;pixels[i+2]=b;pixels[i+3]=swap?c:a;}
 unsigned count=pixels.size()/4,i=0;
 while(i<count){unsigned run=1;while(run<127&&i+run<count && pixels[i*4]==pixels[(i+run)*4] && pixels[i*4+1]==pixels[(i+run)*4+1] && pixels[i*4+2]==pixels[(i+run)*4+2] && pixels[i*4+3]==pixels[(i+run)*4+3])++run;
  if(run>1 || i==count-1){if(!literal.empty()){out.push_back(literal.size()/4);out.insert(out.end(),literal.begin(),literal.end());literal.clear();}out.push_back(run>1?(128|run):1);out.insert(out.end(),pixels.begin()+i*4,pixels.begin()+i*4+4);}
  else{literal.insert(literal.end(),pixels.begin()+i*4,pixels.begin()+i*4+4);if(literal.size()==127*4){out.push_back(127);out.insert(out.end(),literal.begin(),literal.end());literal.clear();}}
  i+=run;
 }
 if(!literal.empty()){out.push_back(literal.size()/4);out.insert(out.end(),literal.begin(),literal.end());}
 unsigned pad=8-out.size()%8;out.insert(out.end(),pad,0);return out;
}
static void resource(unsigned id){require(id==0x01000008||id==0x01000009);}
Bytes checkBody(unsigned id){require(id>=0x01000000&&id<=0x01000009);Bytes b;put32(b,200);put32(b,id);b.push_back(1);return b;}
Bytes removeBody(unsigned id){resource(id);Bytes b;put32(b,200);put32(b,id);return b;}
Bytes bitmapBody(unsigned id,const Bytes& image){resource(id);require(!image.empty()&&image.size()<65500);Bytes b;put32(b,200);put32(b,id);b.push_back(1);put32(b,13+image.size());put32(b,2);put32(b,id);b.push_back(1);put16(b,150);put16(b,36);put32(b,image.size());b.insert(b.end(),image.begin(),image.end());return b;}
Bytes request(unsigned method,unsigned seq,const Bytes& body){require(seq>=1&&seq<=65535&&body.size()<=65536);Bytes b;put16(b,0xb006);put16(b,method);put32(b,body.size()+8);put16(b,0x5348);put16(b,seq);b.push_back(1);b.push_back(1);b.push_back(0);b.push_back(0);b.insert(b.end(),body.begin(),body.end());return b;}
Bytes response(unsigned method,unsigned seq,const Bytes& reply){require(reply.size()>=16&&reply.size()<=65552);Bytes expected=request(method,seq,Bytes());require(reply[0]==expected[0]&&reply[1]==expected[1]&&reply[2]==expected[2]&&reply[3]==expected[3]&&read32(reply,4)==reply.size()-8);for(unsigned i=8;i<14;++i)require(reply[i]==expected[i]);require(reply[14]==128&&reply[15]==0);return Bytes(reply.begin()+16,reply.end());}
}
