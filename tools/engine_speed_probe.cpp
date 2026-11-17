// Bounded read-only probe of the factory Vehicle.EngineSpeed2 property.
// Reference HMI vtable/object establishes function 0xcd0; current registry must
// resolve Vehicle 05/00 to 0x5000. No SET, diagnostic ECU, drawing or coding calls.
#include "dsi_client.hpp"
#include "most/ids.hpp"
#include "most/registry.hpp"
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
using namespace nbt;using namespace nbt::most;
static unsigned long long nowMs(){timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (unsigned long long)t.tv_sec*1000+t.tv_nsec/1000000;}
struct Probe {uint32_t client;uint16_t self;bool registered,registry;unsigned sent,replies;unsigned long long last;
 Probe():client(0),self(0),registered(false),registry(false),sent(0),replies(0),last(0){}
 static void attach(DsiClient*c,void*){std::vector<uint8_t> p;DsiClient::putString(p,"SupraEngineSpeedReadOnly");c->sendRequest(kReqRegisterClient,p);for(unsigned i=0;i<kClientSubscriptionCount;i++)c->setNotification(kClientSubscriptions[i]);}
 static void data(DsiClient*c,uint32_t,uint32_t id,uint32_t,const uint8_t*p,uint32_t len,void*ctx){Probe&o=*(Probe*)ctx;
  if(id==kInfoClientResponse&&len>=6){o.client=rdLe32(p);o.self=rdLe16(p+4);o.registered=o.client!=kClientRefused&&o.self!=0;printf("REGISTER %u %04x\n",o.client,o.self);if(o.registered){std::vector<uint16_t> keys(1,0x0500);c->sendRequest(kReqRegisterDevCtrls,buildRegisterDevCtrls(o.client,keys));}}
  if(id==kAttrRegistry){std::vector<RegistryEntry> entries;if(decodeRegistry(p,len,entries)){const RegistryEntry*r=findRegistryEntry(entries,0x0500);o.registry=r&&r->address==0x5000;printf("REGISTRY vehicle=%04x accepted=%u\n",r?r->address:0,o.registry);}}
  if(id==kInfoMessage){View m;if(parseView(p,len,m)&&m.fblock==5&&m.inst==0&&m.fkt==0xcd0&&m.src==0x5000&&m.dst==o.self&&classify(m)==kNormal&&o.replies<1500){printf("ENGINE %llu op=%u data=",nowMs(),m.op);for(size_t i=0;i<m.len&&i<32;i++)printf("%02x",m.data[i]);puts("");o.replies++;}}
  if(o.registered&&o.registry&&o.sent<12&&nowMs()-o.last>=1000){Msg m;m.txType=0;m.varTag=1;m.varVal=0;m.dst=0x5000;m.src=o.self;m.fblock=5;m.inst=0;m.fkt=0xcd0;m.opType=kOpGet;m.hdrTag=0;std::vector<uint8_t> q;putLe32(q,o.client);std::vector<uint8_t>b=buildMessage(m);q.insert(q.end(),b.begin(),b.end());o.last=nowMs();++o.sent;printf("GET %llu sent=%u success=%u\n",o.last,o.sent,c->sendRequest(kReqProcessMessage,q));}
  fflush(stdout);
 }
};
static void timeout(int){_exit(124);}
int main(int argc,char**argv){if(argc!=2||strcmp(argv[1],"--read-engine-speed"))return 64;signal(SIGALRM,timeout);alarm(130);static Probe p;static DsiClient c;c.setQuiet(true);c.setCallbacks(Probe::attach,Probe::data,&p);if(!c.open(kServerInterface,kServerRole,kInterfaceMajor,kInterfaceMinor))return 2;sleep(120);puts("PROBE_COMPLETE");fflush(stdout);_exit(0);}
