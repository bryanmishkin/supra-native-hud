#include "registry_observer.hpp"
#include "fake_dsi_client.hpp"
#include <assert.h>
#include <stdio.h>
int main() {
    using namespace nbt::most;
    fake_dsi::reset();RegistryObserver o;Client c;assert(o.attach(c));assert(c.start("SupraHudRegistry"));
    fake_dsi::attach();
    unsigned char response[]={1,0,0,0,0x77,0x20};
    fake_dsi::data(kInfoClientResponse,response,sizeof response);
    unsigned char registry[]={2,0,0,0,1,1,0,0x82,2,1,0,0x99};
    fake_dsi::data(kAttrRegistry,registry,sizeof registry);
    assert(o.snapshots==1 && o.counts[0]==2);assert(o.entries[0][0].key==0x8200);assert(o.entries[0][0].address==0x0101);
    fake_dsi::data(kAttrRegistry,registry,5);assert(o.snapshots==1);
    for(unsigned i=0;i<10;++i)fake_dsi::data(kAttrRegistry,registry,sizeof registry);
    assert(o.snapshots==8 && o.dropped==3);
    Msg m={};m.dst=0x0101;m.fblock=0x82;m.inst=0;m.fkt=0x204;m.opType=0;assert(!c.send(m));
    fake_dsi::detach();fake_dsi::attach();
    for(size_t i=0;i<fake_dsi::calls.size();++i)
        if(fake_dsi::calls[i].kind==fake_dsi::Call::kRequest)assert(fake_dsi::calls[i].id==kReqRegisterClient);
    View v={};v.fblock=0x82;v.inst=0;v.src=0x101;v.dst=0x2001;v.fkt=0x204;v.rxMs=123;
    for(unsigned i=0;i<300;++i)RegistryObserver::message(v,kNormal,&o);
    assert(o.headerCount==256&&o.droppedHeaders==44&&o.headers[0].at==123);
    v.fblock=0x99;RegistryObserver::message(v,kNormal,&o);assert(o.droppedHeaders==44);
    assert(c.stats().sent==0);puts("PASS: registry decode, malformed rejection, bounded capture, reconnect, no device registration or HUD send");
}
