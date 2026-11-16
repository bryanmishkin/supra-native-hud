#ifndef SUPRA_REGISTRY_OBSERVER_HPP
#define SUPRA_REGISTRY_OBSERVER_HPP
#include "most/client.hpp"
#include <string.h>
// Subscribe to the registry only. No device-control keys, drawing permissions,
// target function calls, diagnostic requests or HUD objects are registered.
// The upstream client still creates a temporary local DSI client and subscriptions.
struct RegistryObserver {
    enum { kMaxEntries=1024, kMaxSnapshots=8, kMaxHeaders=256 };
    pthread_mutex_t mutex;
    unsigned snapshots, dropped, headerCount, droppedHeaders;
    bool allHeaders;
    struct Header {uint32_t at,tag,len,lastAt,count;uint16_t src,dst,fkt;uint8_t op,fblock,inst;unsigned classification;};
    Header headers[kMaxHeaders];
    size_t counts[kMaxSnapshots];
    nbt::most::RegistryEntry entries[kMaxSnapshots][kMaxEntries];
    RegistryObserver(bool all=false):snapshots(0),dropped(0),headerCount(0),droppedHeaders(0),allHeaders(all) { pthread_mutex_init(&mutex,0); memset(counts,0,sizeof counts); }
    static void message(const nbt::most::View& m, nbt::most::MsgClass c, void* p) {
        RegistryObserver& o=*static_cast<RegistryObserver*>(p);
        if(!o.allHeaders && (m.fblock!=0x82 || m.inst!=0))return;
        pthread_mutex_lock(&o.mutex);
        if(o.allHeaders)for(unsigned n=0;n<o.headerCount;++n) {
            Header& h=o.headers[n];
            if(h.src==m.src&&h.dst==m.dst&&h.fblock==m.fblock&&h.inst==m.inst&&h.fkt==m.fkt&&h.op==m.op&&h.classification==(unsigned)c) {
                ++h.count;h.lastAt=m.rxMs;pthread_mutex_unlock(&o.mutex);return;
            }
        }
        if(o.headerCount>=kMaxHeaders)++o.droppedHeaders;
        else {Header& h=o.headers[o.headerCount++];h.at=h.lastAt=m.rxMs;h.count=1;h.fblock=m.fblock;h.inst=m.inst;h.tag=m.hdrTag;h.len=m.len;h.src=m.src;h.dst=m.dst;h.fkt=m.fkt;h.op=m.op;h.classification=c;}
        pthread_mutex_unlock(&o.mutex);
    }
    static void registry(const std::vector<nbt::most::RegistryEntry>& r,void* p) {
        RegistryObserver& o=*static_cast<RegistryObserver*>(p);
        pthread_mutex_lock(&o.mutex);
        if(o.snapshots>=kMaxSnapshots || r.size()>kMaxEntries) ++o.dropped;
        else { size_t n=o.snapshots++;o.counts[n]=r.size();for(size_t i=0;i<r.size();++i)o.entries[n][i]=r[i]; }
        pthread_mutex_unlock(&o.mutex);
    }
    bool attach(nbt::most::Client& c) {
        return c.setTap(message,this) && c.addRegistryListener(registry,this);
    }
};
#endif
