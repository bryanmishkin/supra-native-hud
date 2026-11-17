#include "factory_stream.hpp"
#include <cassert>
#include <cstdio>
using namespace supra;
static void be(FactoryLease::Packet& p,unsigned at,unsigned n,unsigned bytes){for(unsigned i=0;i<bytes;++i)p[at+i]=(n>>(8*(bytes-i-1)))&255;}
static FactoryLease::Packet msg(unsigned svc,unsigned method,unsigned seq,unsigned client){FactoryLease::Packet p(20,0);be(p,0,svc,2);be(p,2,method,2);be(p,4,12,4);be(p,8,client,2);be(p,10,seq,2);p[12]=p[13]=1;be(p,16,svc==0xb006?200:100,4);return p;}
static FactoryLease::Packet frame(bool out,unsigned seq,unsigned flags,const FactoryLease::Packet& b,unsigned port=40000){FactoryLease::Packet p(54+b.size(),0);be(p,12,0x800,2);p[14]=0x45;be(p,16,40+b.size(),2);p[23]=6;be(p,26,out?0xa030c777:0xa030c760,4);be(p,30,out?0xa030c760:0xa030c777,4);be(p,34,out?port:30502,2);be(p,36,out?30502:port,2);be(p,38,seq,4);p[46]=0x50;p[47]=flags;for(unsigned i=0;i<b.size();++i)p[54+i]=b[i];return p;}
static void feed(FactoryStream& s,const FactoryLease::Packet& p){s.ethernet(&p[0],p.size(),p.size());}
int main(){
 FactoryLease l;FactoryStream s(l);FactoryLease::Packet empty,p=msg(0xb006,4,1,1);assert(l.before(p,0));feed(s,frame(true,100,2,empty));feed(s,frame(false,200,18,empty));
 FactoryLease::Packet a(p.begin(),p.begin()+7),b(p.begin()+7,p.end());feed(s,frame(true,101,16,a));feed(s,frame(true,108,16,b));feed(s,frame(true,108,16,b));assert(!l.failed());
 FactoryLease::Packet ack(p.begin(),p.begin()+16);be(ack,4,8,4);ack[14]=128;feed(s,frame(false,201,16,ack));assert(!l.failed());
 // Unhooked factory traffic and packet loss both revoke admission permanently.
 feed(s,frame(true,121,16,msg(0xb00e,4,2,1)));assert(l.failed());
 FactoryLease own;FactoryStream os(own);feed(os,frame(true,1,2,empty));feed(os,frame(false,1,18,empty));feed(os,frame(true,2,16,msg(0xb006,2,1,0x5348)));feed(os,frame(true,22,17,empty));assert(!own.failed());
 FactoryLease missing;FactoryStream ms(missing);feed(ms,frame(true,5,16,p));assert(missing.failed());
 FactoryLease gap;FactoryStream gs(gap);feed(gs,frame(true,100,2,empty));feed(gs,frame(true,105,16,p));assert(gap.failed());
 FactoryLease repeated;FactoryStream rs(repeated);
 for(unsigned port=41000;port<41040;++port){feed(rs,frame(true,1,2,empty,port));feed(rs,frame(false,1,18,empty,port));rs.registerOwn(0xa030c777,port);feed(rs,frame(true,2,17,empty,port));feed(rs,frame(false,2,16,empty,port));feed(rs,frame(false,2,17,empty,port));feed(rs,frame(true,3,16,empty,port));assert(!repeated.failed());}
 FactoryLease idleCookie;FactoryStream cs(idleCookie);FactoryLease::Packet cookie(16,0);be(cookie,0,0xffff8000,4);be(cookie,4,8,4);be(cookie,8,0xdeadbeef,4);cookie[12]=cookie[13]=1;cookie[14]=2;feed(cs,frame(false,900,24,cookie));assert(!idleCookie.failed());assert(!idleCookie.available());cookie[8]=0;feed(cs,frame(false,916,24,cookie));assert(idleCookie.failed());
 FactoryLease unused;FactoryStream us(unused);feed(us,frame(true,1,2,empty));feed(us,frame(true,1,4,empty));assert(!unused.failed());assert(!unused.available());
 FactoryLease used;FactoryStream usedStream(used);FactoryLease::Packet usedRequest=msg(0xb006,4,99,1);assert(used.before(usedRequest,0));feed(usedStream,frame(true,1,2,empty));feed(usedStream,frame(true,2,16,usedRequest));feed(usedStream,frame(false,5,4,empty));assert(used.failed());
 puts("factory stream tests passed");
}
