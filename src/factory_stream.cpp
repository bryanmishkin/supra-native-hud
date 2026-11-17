#include "factory_stream.hpp"
#include <cstring>
namespace supra {
static unsigned u16(const unsigned char* p){return unsigned(p[0])*256+p[1];}
static unsigned u32(const unsigned char* p){return (unsigned(p[0])<<24)|(unsigned(p[1])<<16)|(unsigned(p[2])<<8)|p[3];}
void FactoryStream::registerOwn(unsigned address,unsigned port){
 unsigned char k[12];unsigned addresses[2]={address,0xa030c760};for(unsigned d=0;d<2;++d){for(unsigned j=0;j<2;++j)for(unsigned i=0;i<4;++i)k[j*4+i]=(addresses[j^d]>>(24-8*i))&255;unsigned ports[2]={d?30502:port,d?port:30502};for(unsigned j=0;j<2;++j){k[8+j*2]=ports[j]>>8;k[9+j*2]=ports[j]&255;}flows_[std::string((const char*)k,12)].own=true;}
}
void FactoryStream::ethernet(const unsigned char* p,unsigned n,unsigned wire){
 if(!p||n!=wire||n<14){lease_.fault("truncated capture");return;}
 unsigned off=14,type=u16(p+12);
 for(unsigned i=0;i<2&&(type==0x8100||type==0x88a8);++i){if(n<off+4){lease_.fault("VLAN truncation");return;}type=u16(p+off+2);off+=4;}
 if(type!=0x800)return;
 if(n<off+20||(p[off]>>4)!=4){lease_.fault("IPv4 truncation");return;}
 unsigned ihl=(p[off]&15)*4,total=u16(p+off+2);bool outgoing=u32(p+off+16)==0xa030c760,incoming=u32(p+off+12)==0xa030c760;
 if(p[off+9]!=6||(!outgoing&&!incoming))return;
 if(ihl<20||total<ihl+20||off+total>n||(u16(p+off+6)&0x3fff)){lease_.fault("fragmented/truncated factory TCP");return;}
 unsigned tcp=off+ihl,thl=(p[tcp+12]>>4)*4;
 if(thl<20||total<ihl+thl){lease_.fault("TCP header");return;}
 if((outgoing?u16(p+tcp+2):u16(p+tcp))!=30502)return;
 unsigned length=total-ihl-thl,seq=u32(p+tcp+4),flags=p[tcp+13];
 std::string key((const char*)p+off+12,8);key.append((const char*)p+tcp,4);
 // A warm head-unit restart can leave a cluster keepalive on an older TCP
 // connection. An exact standalone cookie carries no model state and cannot
 // establish sequence tracking or grant admission. Tracked streams still consume it.
 const unsigned char* payload=p+tcp+thl;
 if(!flows_.count(key)&&incoming&&length==16&&u32(payload)==0xffff8000&&u32(payload+4)==8&&u32(payload+8)==0xdeadbeef&&payload[12]==1&&payload[13]==1&&(payload[14]==2||payload[14]==128)&&payload[15]==0)return;
 if(!flows_.count(key)&&!(flags&2)&&(!length||(flags&5)))return;
 if(!flows_.count(key)&&flows_.size()>=16){lease_.fault("flow limit");return;}
 Flow& f=flows_[key];
 if(flags&2){if(f.shared){lease_.fault("active factory connection replaced");return;}f.established=true;f.next=seq+1;f.bytes.clear();seq++;}
 if(flags&5){if(!f.own&&(f.shared||!f.bytes.empty()))lease_.fault("factory transport closed");flows_.erase(key);return;}
 if(f.own)return;
 if(!length)return;
 if(!f.established){lease_.fault("capture began midstream");return;}
 int delta=(int)(seq-f.next);
 if(delta<0){unsigned overlap=f.next-seq;if(overlap>=length)return;lease_.fault("overlapping factory segment");return;}
 if(delta>0){lease_.fault("missing/out-of-order factory segment");return;}
 if(f.bytes.size()+length>131104){lease_.fault("stream bound");return;}
 f.next+=length;f.bytes.insert(f.bytes.end(),p+tcp+thl,p+tcp+thl+length);
 while(f.bytes.size()>=16){
  unsigned size=u32(&f.bytes[4]);if(size<8||size>65544){lease_.fault("stream framing");return;}size+=8;if(f.bytes.size()<size)break;
  FactoryLease::Packet msg(f.bytes.begin(),f.bytes.begin()+size);f.bytes.erase(f.bytes.begin(),f.bytes.begin()+size);
  if(u16(&msg[0])==65535&&size==16&&u32(&msg[8])==0xdeadbeef)continue;
  if(u16(&msg[8])==0x5348){f.own=true;f.bytes.clear();std::string reverse((const char*)p+off+16,4);reverse.append((const char*)p+off+12,4);reverse.append((const char*)p+tcp+2,2);reverse.append((const char*)p+tcp,2);flows_[reverse].own=true;return;}
  f.shared=true;std::string other((const char*)p+off+16,4);other.append((const char*)p+off+12,4);other.append((const char*)p+tcp+2,2);other.append((const char*)p+tcp,2);flows_[other].shared=true;
  if(outgoing)lease_.outgoing(msg);else lease_.reply(msg);
 }
}
}
