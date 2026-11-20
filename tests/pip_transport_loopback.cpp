// Test executable permits loopback only. Not a vehicle launcher.
#include "displaysink_transport.hpp"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char** argv) {
    if(argc!=4 && argc!=5) return 2;
    supra_pip::DisplaySink sink(argc==5 && !strcmp(argv[4],"hud-candidate"));
    if(!sink.open("127.0.0.1","127.0.0.1",atoi(argv[1]),atoi(argv[2]),atoi(argv[3]))) return 3;
    int reported=-1;
    while(sink.pump()) {
        if(sink.negotiated_cluster() && reported!=1) { puts("NEGOTIATED_CLUSTER");fflush(stdout);reported=1; }
        if(sink.negotiated_hud() && reported!=0) { puts("NEGOTIATED_HUD_CANDIDATE");fflush(stdout);reported=0; }
    }
    puts("TRANSPORT_CLOSED");
    return 0;
}
