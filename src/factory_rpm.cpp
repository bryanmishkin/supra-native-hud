#include "factory_rpm.hpp"
#include "dsi_client.hpp"
#include "most/registry.hpp"
#include <pthread.h>
#include <time.h>
namespace supra {
using namespace nbt;using namespace nbt::most;
namespace {
uint64_t clockMs(){timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return 0;return uint64_t(t.tv_sec)*1000+t.tv_nsec/1000000;}
struct Feed {
 pthread_mutex_t lock;DsiClient client;uint32_t id;uint16_t self;bool registered,registry,requested;Sample sample;
 Feed():id(0),self(0),registered(false),registry(false),requested(false){pthread_mutex_init(&lock,0);}
 static void attached(DsiClient*c,void*){std::vector<uint8_t> p;DsiClient::putString(p,"SupraFactoryRpm");c->sendRequest(kReqRegisterClient,p);for(unsigned i=0;i<kClientSubscriptionCount;++i)c->setNotification(kClientSubscriptions[i]);}
 static void detached(DsiClient*,void* ctx){Feed& f=*(Feed*)ctx;pthread_mutex_lock(&f.lock);f.sample=Sample();f.registered=f.registry=f.requested=false;pthread_mutex_unlock(&f.lock);}
 static void data(DsiClient*c,uint32_t,uint32_t attr,uint32_t,const uint8_t*p,uint32_t n,void*ctx){
  Feed& f=*(Feed*)ctx;bool subscribe=false,request=false;uint32_t clientId=0;uint16_t own=0;
  pthread_mutex_lock(&f.lock);
  if(attr==kInfoClientResponse&&n>=6){f.id=rdLe32(p);f.self=rdLe16(p+4);f.registered=f.id!=kClientRefused&&f.self!=0;f.sample=Sample();subscribe=f.registered;}
  if(attr==kAttrRegistry){std::vector<RegistryEntry> entries;bool ok=decodeRegistry(p,n,entries);const RegistryEntry*r=ok?findRegistryEntry(entries,0x0500):0;f.registry=r&&r->address==0x5000;if(!f.registry){f.sample=Sample();f.requested=false;}}
  if(attr==kInfoMessage&&f.registered&&f.registry){View m;if(parseView(p,n,m))decodeFactoryRpm(m,f.self,clockMs(),f.sample);}
  if(f.registered&&f.registry&&!f.requested){request=true;f.requested=true;}
  clientId=f.id;own=f.self;pthread_mutex_unlock(&f.lock);
  // No DSI calls under our mutex: a callback may be reentrant.
  if(subscribe){std::vector<uint16_t> keys(1,0x0500);c->sendRequest(kReqRegisterDevCtrls,buildRegisterDevCtrls(clientId,keys));}
  if(request){Msg m;m.txType=0;m.varTag=1;m.varVal=0;m.dst=0x5000;m.src=own;m.fblock=5;m.inst=0;m.fkt=0xcd0;m.opType=kOpGet;m.hdrTag=0;std::vector<uint8_t> q;putLe32(q,clientId);std::vector<uint8_t>b=buildMessage(m);q.insert(q.end(),b.begin(),b.end());c->sendRequest(kReqProcessMessage,q);}
 }
};
// Process-lifetime object; DSI callbacks must never outlive their storage.
Feed* feed=0;
}
bool startFactoryRpm(){if(feed)return true;feed=new Feed;feed->client.setQuiet(true);feed->client.setQuietTx(true);feed->client.setCallbacks(Feed::attached,Feed::data,feed);feed->client.setDetachCallback(Feed::detached);return feed->client.open(kServerInterface,kServerRole,kInterfaceMajor,kInterfaceMinor);}
Sample latestFactoryRpm(){if(!feed)return Sample();pthread_mutex_lock(&feed->lock);Sample s=feed->sample;pthread_mutex_unlock(&feed->lock);return s;}
}
