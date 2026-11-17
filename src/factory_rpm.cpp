#include "factory_rpm.hpp"
#include "dsi_client.hpp"
#include "most/registry.hpp"
#include <pthread.h>
#include <time.h>
#include <unistd.h>
namespace supra {
using namespace nbt;using namespace nbt::most;
namespace {
uint64_t clockMs(){timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return 0;return uint64_t(t.tv_sec)*1000+t.tv_nsec/1000000;}
struct Feed {
 pthread_mutex_t lock,sendLock;DsiClient client;uint32_t id;uint16_t self;bool registered,registry,subscribed;uint64_t lastRequest;Sample sample;
 Feed():id(0),self(0),registered(false),registry(false),subscribed(false),lastRequest(0){pthread_mutex_init(&lock,0);pthread_mutexattr_t a;pthread_mutexattr_init(&a);pthread_mutexattr_settype(&a,PTHREAD_MUTEX_RECURSIVE);pthread_mutex_init(&sendLock,&a);pthread_mutexattr_destroy(&a);}
 static void attached(DsiClient*c,void*ctx){Feed& f=*(Feed*)ctx;pthread_mutex_lock(&f.sendLock);std::vector<uint8_t> p;DsiClient::putString(p,"SupraFactoryRpm");c->sendRequest(kReqRegisterClient,p);for(unsigned i=0;i<kClientSubscriptionCount;++i)c->setNotification(kClientSubscriptions[i]);pthread_mutex_unlock(&f.sendLock);}
 static void detached(DsiClient*,void* ctx){Feed& f=*(Feed*)ctx;pthread_mutex_lock(&f.lock);f.sample=Sample();f.registered=f.registry=f.subscribed=false;f.lastRequest=0;pthread_mutex_unlock(&f.lock);}
 static void data(DsiClient*c,uint32_t,uint32_t attr,uint32_t,const uint8_t*p,uint32_t n,void*ctx){
  Feed& f=*(Feed*)ctx;bool subscribe=false;uint32_t clientId=0;
  pthread_mutex_lock(&f.lock);
  if(attr==kInfoClientResponse&&n>=6){f.id=rdLe32(p);f.self=rdLe16(p+4);f.registered=f.id!=kClientRefused&&f.self!=0;f.sample=Sample();f.subscribed=false;subscribe=f.registered;}
  if(attr==kAttrRegistry){std::vector<RegistryEntry> entries;bool ok=decodeRegistry(p,n,entries);const RegistryEntry*r=ok?findRegistryEntry(entries,0x0500):0;f.registry=r&&r->address==0x5000;if(!f.registry){f.sample=Sample();f.lastRequest=0;}}
  if(attr==kInfoMessage&&f.registered&&f.registry){View m;if(parseView(p,n,m))decodeFactoryRpm(m,f.self,clockMs(),f.sample);}
  clientId=f.id;pthread_mutex_unlock(&f.lock);
  // No DSI calls under our mutex: a callback may be reentrant.
  if(subscribe){std::vector<uint16_t> keys(1,0x0500);pthread_mutex_lock(&f.sendLock);bool ok=c->sendRequest(kReqRegisterDevCtrls,buildRegisterDevCtrls(clientId,keys));pthread_mutex_unlock(&f.sendLock);pthread_mutex_lock(&f.lock);f.subscribed=ok&&f.registered&&f.id==clientId;pthread_mutex_unlock(&f.lock);}
 }
 static void* poll(void* ctx){
  Feed& f=*(Feed*)ctx;
  for(;;){
   pthread_mutex_lock(&f.lock);uint64_t t=clockMs();bool ready=f.registered&&f.registry&&f.subscribed&&t>=f.lastRequest&&t-f.lastRequest>=100;uint32_t clientId=f.id;uint16_t own=f.self;if(ready)f.lastRequest=t;pthread_mutex_unlock(&f.lock);
   if(ready){Msg m;m.txType=0;m.varTag=1;m.varVal=0;m.dst=0x5000;m.src=own;m.fblock=5;m.inst=0;m.fkt=0xcd0;m.opType=kOpGet;m.hdrTag=0;std::vector<uint8_t> q;putLe32(q,clientId);std::vector<uint8_t>b=buildMessage(m);q.insert(q.end(),b.begin(),b.end());pthread_mutex_lock(&f.sendLock);bool ok=f.client.sendRequest(kReqProcessMessage,q);pthread_mutex_unlock(&f.sendLock);if(!ok){pthread_mutex_lock(&f.lock);f.sample=Sample();pthread_mutex_unlock(&f.lock);}}
   usleep(10000);
  }
  return 0;
 }

};
// Process-lifetime object; DSI callbacks must never outlive their storage.
Feed* feed=0;
}
bool startFactoryRpm(){if(feed)return true;feed=new Feed;feed->client.setQuiet(true);feed->client.setQuietTx(true);feed->client.setCallbacks(Feed::attached,Feed::data,feed);feed->client.setDetachCallback(Feed::detached);if(!feed->client.open(kServerInterface,kServerRole,kInterfaceMajor,kInterfaceMinor))return false;pthread_t t;if(pthread_create(&t,0,Feed::poll,feed))return false;pthread_detach(t);return true;}
Sample latestFactoryRpm(){if(!feed)return Sample();pthread_mutex_lock(&feed->lock);Sample s=feed->sample;pthread_mutex_unlock(&feed->lock);return s;}
}
