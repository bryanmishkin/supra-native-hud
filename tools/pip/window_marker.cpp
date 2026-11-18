// Bounded RAM-only native producer; never sends Guidance/DisplaySink requests.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <errno.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>
#include "native_screen.hpp"

uint32_t nbt::cluster::VideoProfile::maneuver=0;
static volatile sig_atomic_t stopped=0;
static void stop(int) { stopped=1; }
static bool contains(const char* path,const char* required) {
    FILE* f=fopen(path,"rb"); if(!f) return false;
    char b[8193]; size_t n=fread(b,1,sizeof(b)-1,f);
    bool valid=!ferror(f) && n<sizeof(b)-1; fclose(f); b[n]=0;
    return valid && strstr(b,required)!=0;
}
static bool absent(const char* path) {
    struct stat s; return lstat(path,&s)!=0 && errno==ENOENT;
}
static bool v1_quiet() {
    return contains("/tmp/supra-hud-v1/resident.status","STOPPED\n") &&
        absent("/tmp/supra-hud-v1/factory.sock") &&
        absent("/tmp/supra-hud-v1/active.jsonl.handoff");
}
static bool admission() {
    // Read-only live admission; these paths are from retained target evidence.
    return v1_quiet() &&
        contains("/dev/screen/0/dpy-2","device_id = OTHER2\n") &&
        contains("/dev/screen/0/dpy-2","video mode = 800 x 480 @") &&
        contains("/dev/screen/0/dpy-2","scene = (empty)\n") &&
        contains("/dev/screen/0/dpy-2","windows = (none)\n");
}
static unsigned long long milliseconds() {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC,&t)) return 0;
    return (unsigned long long)t.tv_sec*1000+t.tv_nsec/1000000;
}

int main(int argc,char** argv) {
    if (argc!=4 || strcmp(argv[1],"--parked-experiment")) {
        puts("No drawing. Usage: window-marker --parked-experiment <description-id-decimal> /tmp/supra-pip-<run>/stop");
        return argc==1 ? 0 : 2;
    }
    char* end=0;
    unsigned long id=strtoul(argv[2],&end,10);
    if (!*argv[2] || *end || id!=0x0f000004ul) return 2;
    if(strncmp(argv[3],"/tmp/supra-pip-",15) || strstr(argv[3],"..") ||
        strlen(argv[3])>160 || !absent(argv[3])) return 2;
    if(!admission()) { puts("REFUSE: V1 not quiet or secondary output occupied/unknown");return 3; }
    nbt::cluster::VideoProfile::maneuver=id;
    signal(SIGINT,stop); signal(SIGTERM,stop); signal(SIGALRM,stop);
    alarm(35);
    setvbuf(stdout,0,_IONBF,0);
    kombi::pip::screen::ScreenOutput out={0,0,0,0,0};
    out.metadata_profile=kombi::pip::screen::FactoryManeuver;
    bool ok=out.inspect(1) && out.create();
    unsigned char image[320*200*4];
    // Asymmetric marker: white border/cross, cyan left, orange right corners.
    for (unsigned y=0;y<200;++y) for (unsigned x=0;x<320;++x) {
        unsigned char* p=image+(y*320+x)*4;
        bool edge=x<4 || x>=316 || y<4 || y>=196;
        bool cross=(x>=158 && x<162) || (y>=98 && y<102);
        p[0]=p[1]=p[2]=(edge||cross)?200:0; p[3]=255;
        if(x>=12 && x<52 && y>=12 && y<52) { p[0]=220;p[1]=180;p[2]=0; }
        if(x>=268 && x<308 && y>=148 && y<188) { p[0]=0;p[1]=110;p[2]=220; }
    }
    unsigned long long start=milliseconds();
    if (!start) ok=false;
    unsigned frame=0;
    // Thirty seconds independent of the laptop. Unknown/hung IPC is NOT clean.
    while(ok && !stopped && absent(argv[3]) && milliseconds()-start<30000) {
        if(!v1_quiet()) { puts("V1_STATE_CHANGED");ok=false;break; }
        ok=out.present(image,++frame,false);
        if(frame==1 && ok) puts("PRODUCER_READY");
        usleep(100000);
    }
    bool closed=out.close(); alarm(0);
    printf("PRODUCER_END frames=%u producer_ok=%u local_cleanup=%u\n",frame,unsigned(ok),unsigned(closed));
    // Caller must separately withdraw Guidance, dispose its PiP resource,
    // check absence and obtain visual confirmation. This proves none of those.
    return ok && closed ? 0 : 1;
}
