// Read-only observation of messages delivered by the factory MOST service.
// No target GET/SET, firmware, drawing, or device registration requests.
#include "most/client.hpp"
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <string.h>
using namespace nbt::most;
static void timeout(int){_exit(124);}
struct Capture {
 pthread_mutex_t mutex; unsigned count,dropped; bool provider;
 struct Row {uint32_t ms,len;uint16_t src,dst,fkt;uint8_t fb,inst,op,cls,data[128];};
 Row rows[4096];
 Capture():count(0),dropped(0),provider(false){pthread_mutex_init(&mutex,0);}
 static void registry(const std::vector<RegistryEntry>& r,void* v){Capture& c=*(Capture*)v;const RegistryEntry* p=findRegistryEntry(r,0xe001);pthread_mutex_lock(&c.mutex);c.provider=p&&p->address==0x5000;pthread_mutex_unlock(&c.mutex);}
 static void data(const View&m,MsgClass cls,void*v){
  if(m.fblock!=0xe0)return;
  Capture& c=*(Capture*)v;pthread_mutex_lock(&c.mutex);
  if(c.count==4096||m.len>128){++c.dropped;pthread_mutex_unlock(&c.mutex);return;}
  Row& r=c.rows[c.count++];r.ms=m.rxMs;r.len=m.len;r.src=m.src;r.dst=m.dst;r.fkt=m.fkt;r.fb=m.fblock;r.inst=m.inst;r.op=m.op;r.cls=cls;if(m.len)memcpy(r.data,m.data,m.len);pthread_mutex_unlock(&c.mutex);
 }
};
int main(int argc,char**argv){
 if(argc!=2||strcmp(argv[1],"--observe-hud-control"))return 64;
 setvbuf(stdout,0,_IONBF,0);signal(SIGALRM,timeout);alarm(130);static Capture c;static Client client;
 if(!client.setTap(Capture::data,&c)||!client.addRegistryListener(Capture::registry,&c)||!client.addDevCtrl(0xe001)||!client.start("SupraHudControlObserve"))return 2;
 puts("OBSERVER_STARTED duration=120 target_commands=0");fflush(stdout);
 for(unsigned i=0;i<120;++i)sleep(1);
 ClientStats stats=client.stats();pthread_mutex_lock(&c.mutex);
 printf("{\"provider_e001_5000\":%s,\"target_commands_sent\":%u,\"dropped\":%u,\"bad\":%u,\"rows\":[",c.provider?"true":"false",stats.sent,c.dropped,stats.bad);
 for(unsigned i=0;i<c.count;++i){const Capture::Row&r=c.rows[i];printf("%s{\"ms\":%u,\"source\":%u,\"destination\":%u,\"function\":%u,\"fblock\":%u,\"instance\":%u,\"operation\":%u,\"class\":%u,\"data\":\"",i?",":"",r.ms,r.src,r.dst,r.fkt,r.fb,r.inst,r.op,r.cls);for(unsigned j=0;j<r.len;++j)printf("%02x",r.data[j]);printf("\"}");}
 printf("]}\n");fflush(stdout);_exit(c.dropped||stats.bad||stats.sent?3:0);
}
