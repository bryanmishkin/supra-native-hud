#include "background_traffic.hpp"
#include "factory_lease.hpp"
#include <cassert>
#include <cstdio>
using namespace supra;
typedef FactoryLease::Packet B;
static void put(B& b,unsigned v,unsigned n){for(int i=n-1;i>=0;--i)b.push_back((v>>(i*8))&255);}
static B packet(unsigned method,unsigned seq,const B& body){B b;put(b,0xb006,2);put(b,method,2);put(b,body.size()+8,4);put(b,1,2);put(b,seq,2);put(b,0x01010000,4);b.insert(b.end(),body.begin(),body.end());return b;}
static B remove(unsigned id,unsigned seq){B b;put(b,200,4);put(b,id,4);return packet(8,seq,b);}
static B frame(const B& p,unsigned seq){B b(12,0);put(b,0x800,2);b.push_back(0x45);b.push_back(0);put(b,40+p.size(),2);put(b,0,4);b.push_back(64);b.push_back(6);put(b,0,2);put(b,0xa030c777,4);put(b,0xa030c760,4);put(b,44000,2);put(b,30502,2);put(b,seq,4);put(b,0,4);put(b,0x5018,2);put(b,1000,2);put(b,0,4);b.insert(b.end(),p.begin(),p.end());return b;}
static bool feed(BackgroundTraffic& g,const B& b){return g.consume(&b[0],b.size(),b.size());}
static B model(unsigned id,unsigned type,unsigned seq){B b;put(b,200,4);put(b,id,4);put(b,type,1);put(b,5,4);put(b,1,4);put(b,id,4);put(b,type,1);return packet(9,seq,b);}
int main(){
 B text=remove(0x03000004,32),bitmap=remove(0x01000008,33),road=model(0x11000000,17,34),main=model(0x21000000,33,35);
 assert(backgroundFactoryRequest(&text[0],text.size()));assert(backgroundFactoryRequest(&road[0],road.size()));assert(!backgroundFactoryRequest(&bitmap[0],bitmap.size()));assert(!backgroundFactoryRequest(&main[0],main.size()));
 BackgroundTraffic no;assert(!feed(no,frame(text,100)));
 BackgroundTraffic a;assert(a.authorize(&text[0],text.size()));assert(!a.authorize(&text[0],text.size()));assert(!a.authorize(&bitmap[0],bitmap.size()));
 for(size_t i=0;i<text.size();++i){B one(1,text[i]);assert(feed(a,frame(one,100+i)));}
 assert(a.pendingAuthorizations()==0);assert(feed(a,frame(text,100)));
 B changed=text;changed[23]^=1;assert(!feed(a,frame(changed,100)));
 BackgroundTraffic combined;assert(combined.authorize(&text[0],text.size()));assert(combined.authorize(&road[0],road.size()));B both=text;both.insert(both.end(),road.begin(),road.end());assert(feed(combined,frame(both,200)));assert(combined.pendingAuthorizations()==0);
 BackgroundTraffic gap;assert(gap.authorize(&text[0],text.size()));B first(text.begin(),text.begin()+7),last(text.begin()+7,text.end());assert(feed(gap,frame(first,500)));assert(!feed(gap,frame(last,508)));
 BackgroundTraffic overlap;assert(overlap.authorize(&text[0],text.size()));assert(feed(overlap,frame(first,500)));assert(feed(overlap,frame(text,500)));
 BackgroundTraffic mixed;assert(mixed.authorize(&text[0],text.size()));both=text;both.insert(both.end(),main.begin(),main.end());assert(!feed(mixed,frame(both,300)));
 BackgroundTraffic cookies;assert(cookies.authorize(&text[0],text.size()));B cookie;put(cookie,0xffff0000,4);put(cookie,8,4);put(cookie,0xdeadbeef,4);put(cookie,0x01010100,4);assert(feed(cookies,frame(cookie,900)));assert(feed(cookies,frame(text,916)));
 BackgroundTraffic corrupted;B invalid=text;invalid[7]++;assert(!corrupted.authorize(&invalid[0],invalid.size()));
 FactoryLease l;assert(l.before(text,0));assert(l.outgoing(text));B reply(text.begin(),text.begin()+16);reply[7]=8;reply[14]=129;reply[15]=1;assert(l.reply(reply));assert(!l.failed()&&l.backgroundFailures==1&&l.failedRequest==text&&l.failedReply==reply);assert(!l.available());
 FactoryLease dangerous;assert(dangerous.before(bitmap,0));assert(dangerous.outgoing(bitmap));reply.assign(bitmap.begin(),bitmap.begin()+16);reply[7]=8;reply[14]=129;reply[15]=1;assert(!dangerous.reply(reply)&&dangerous.failed());
 puts("background authorization, fragmentation, retransmission, mixed traffic and namespace tests passed");
}
