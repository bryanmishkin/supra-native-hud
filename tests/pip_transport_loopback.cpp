// Test executable permits loopback only. Not a vehicle launcher.
#include "displaysink_transport.hpp"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char** argv) {
    if(argc!=4) return 2;
    supra_pip::DisplaySink sink;
    if(!sink.open("127.0.0.1","127.0.0.1",atoi(argv[1]),atoi(argv[2]),atoi(argv[3]))) return 3;
    bool reported=false;
    while(sink.pump()) {
        if(sink.negotiated_cluster() && !reported) { puts("NEGOTIATED_CLUSTER");fflush(stdout);reported=true; }
    }
    puts("TRANSPORT_CLOSED");
    return 0;
}
