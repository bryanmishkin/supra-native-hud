#include "registry_observer.hpp"
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
static volatile sig_atomic_t interrupted=0;
static void stop(int) { interrupted=1; }
static void deadline(int) { _exit(124); }
static unsigned long elapsed(const timespec& a,const timespec& b) {
    return (unsigned long)((b.tv_sec-a.tv_sec)*1000+(b.tv_nsec-a.tv_nsec)/1000000);
}
int main(int argc,char** argv) {
    bool allHeaders=argc==3 && !strcmp(argv[2],"--all-headers");
    if((argc!=2 && !allHeaders) || strcmp(argv[1],"--observe-registry")) {
        fprintf(stderr,"Registry observer requires --observe-registry; runtime 15 seconds; optional --all-headers\n");return 64;
    }
    signal(SIGINT,stop);signal(SIGTERM,stop);signal(SIGALRM,deadline);alarm(20);
    timespec began,ended;if(clock_gettime(CLOCK_MONOTONIC,&began))return 4;
    static RegistryObserver observer(allHeaders);
    static nbt::most::Client client;
    if(!observer.attach(client) || !client.start("SupraHudRegistry"))return 2;
    for(unsigned i=0;i<15 && !interrupted;++i)sleep(1);
    // End the process while the vendor callback thread still owns its objects.
    // Do not destruct a client whose upstream API has no stop/join contract.
    if(clock_gettime(CLOCK_MONOTONIC,&ended))_exit(4);
    nbt::most::ClientStats stats=client.stats();
    nbt::most::LinkState state=client.state();
    unsigned self=client.selfAddress();
    pthread_mutex_lock(&observer.mutex);
    printf("{\"schema\":2,\"snapshots\":[");
    for(unsigned n=0;n<observer.snapshots;++n) {
        if(n)putchar(',');
        putchar('[');
        for(size_t i=0;i<observer.counts[n];++i) {
            if(i)putchar(',');
            printf("{\"address\":%u,\"key\":%u}",observer.entries[n][i].address,observer.entries[n][i].key);
        }
        putchar(']');
    }
    printf("],\"dropped_snapshots\":%u,\"hud_commands_sent\":%u,\"elapsed_ms\":%lu,\"link_state\":\"%s\",\"self_address\":%u,\"message_count\":%u,\"bad_messages\":%u,\"headers\":[",observer.dropped,stats.sent,elapsed(began,ended),nbt::most::linkStateName(state),self,stats.msgs,stats.bad);
    for(unsigned n=0;n<observer.headerCount;++n) {
        const RegistryObserver::Header& h=observer.headers[n];
        printf("%s{\"rx_ms_u32\":%u,\"source\":%u,\"destination\":%u,\"function\":%u,\"operation\":%u,\"tag\":%u,\"bytes\":%u,\"class\":%u,\"fblock\":%u,\"instance\":%u,\"count\":%u,\"last_rx_ms_u32\":%u}",n?",":"",h.at,h.src,h.dst,h.fkt,h.op,h.tag,h.len,h.classification,h.fblock,h.inst,h.count,h.lastAt);
    }
    printf("],\"dropped_headers\":%u,\"payloads_captured\":false,\"all_headers\":%s}\n",observer.droppedHeaders,allHeaders?"true":"false");
    unsigned count=observer.snapshots;
    pthread_mutex_unlock(&observer.mutex);fflush(stdout);_exit(count?0:3);
}
