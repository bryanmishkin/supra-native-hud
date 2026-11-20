// Experimental owned producer. Selection1 is a cluster lease, NOT HUD routing proof.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <errno.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>
#include "screen_output.hpp"
#include "displaysink_transport.hpp"
static volatile sig_atomic_t stopped=0;
static void stop(int){stopped=1;}
static unsigned long long ms(){timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t)){stopped=1;return 0;}return (unsigned long long)t.tv_sec*1000+t.tv_nsec/1000000;}
static bool absent(const char*p){struct stat s;return lstat(p,&s)!=0&&errno==ENOENT;}
static bool contains(const char*p,const char*x){FILE*f=fopen(p,"rb");if(!f)return false;char b[8193];size_t n=fread(b,1,8192,f);bool ok=!ferror(f)&&n<8192;fclose(f);b[n]=0;return ok&&strstr(b,x);}
static bool quiet(){return contains("/tmp/supra-hud-v1/resident.status","STOPPED\n")&&absent("/tmp/supra-hud-v1/factory.sock")&&absent("/tmp/supra-hud-v1/active.jsonl.handoff");}
static bool admission(){return quiet()&&contains("/dev/screen/0/dpy-2","device_id = OTHER2\n")&&contains("/dev/screen/0/dpy-2","video mode = 800 x 480 @")&&contains("/dev/screen/0/dpy-2","scene = (empty)\n")&&contains("/dev/screen/0/dpy-2","windows = (none)\n");}
static bool go_file(const char*p){struct stat s;return !lstat(p,&s)&&S_ISREG(s.st_mode)&&s.st_uid==geteuid()&&s.st_size==0;}
static void snapshot(const char*phase){
 printf("ACTIVE_OUTPUT_BEGIN phase=%s\n",phase);FILE*f=fopen("/dev/screen/0/dpy-2","rb");
 if(!f){puts("ACTIVE_OUTPUT_END unavailable=1");return;}
 char b[8192];size_t n=fread(b,1,sizeof(b),f);fwrite(b,1,n,stdout);
 printf("\nACTIVE_OUTPUT_END read_error=%u truncated=%u\n",unsigned(ferror(f)!=0),unsigned(n==sizeof(b)));fclose(f);
}
static unsigned number(const char*p){char*e=0;unsigned long n=strtoul(p,&e,10);return *p&&!*e&&n<=0xfffffffful?unsigned(n):0;}
int main(int argc,char**argv){
 const bool hud_candidate=argc==10&&!strcmp(argv[9],"--observe-hud-selection");
 if((argc!=9&&!hud_candidate)||strcmp(argv[1],"--parked-experiment")){puts("No drawing. Usage: corrected-marker --parked-experiment 251658244 day|night /tmp/supra-pip-corrected-<hexrun> producerIPv4 receiverIPv4 sinkPort sdPort");return argc==1?0:2;}
 unsigned id=number(argv[2]),sinkport=number(argv[7]),sdport=number(argv[8]);
 int style=!strcmp(argv[3],"day")?1:!strcmp(argv[3],"night")?0:-1;
 const char*prefix="/tmp/supra-pip-corrected-";const size_t plen=strlen(prefix);const char*token=0;
 if(id!=0x0f000004||style<0||strncmp(argv[4],prefix,plen)||strlen(argv[4])<plen+16||strlen(argv[4])>plen+32||!sinkport||sinkport>65535||!sdport||sdport>65535)return 2;
 token=argv[4]+plen;
 for(const char*p=token;*p;++p)if(!((*p>='0'&&*p<='9')||(*p>='a'&&*p<='f')))return 2;
 struct stat st;if(lstat(argv[4],&st)||!S_ISDIR(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&077)!=0)return 2;
 char go[180],halt[180],wid[80];snprintf(go,sizeof(go),"%s/go",argv[4]);snprintf(halt,sizeof(halt),"%s/stop",argv[4]);snprintf(wid,sizeof(wid),"268444457");
 if(!absent(go)||!absent(halt)||!admission())return 3;
 setvbuf(stdout,0,_IONBF,0);signal(SIGINT,stop);signal(SIGTERM,stop);signal(SIGALRM,stop);signal(SIGPIPE,SIG_IGN);alarm(45);
 unsigned long long start=ms();if(!start)return 3;
 supra_pip::DisplaySink sink(hud_candidate);
 bool ok=sink.open(argv[5],argv[6],sinkport,sdport,45);
 while(ok&&!stopped&&ms()-start<4000&&!(sink.negotiated_cluster()||(hud_candidate&&sink.negotiated_hud())))ok=sink.pump();
 ok=ok&&!stopped&&(sink.negotiated_cluster()||(hud_candidate&&sink.negotiated_hud()))&&admission();
 if(ok)puts(sink.negotiated_hud()?"SINK_NEGOTIATED_HUD_CANDIDATE":"SINK_NEGOTIATED_CLUSTER");
 // No Screen API before valid lease and an explicitly admitted received tuple.
 unsigned last_sink=sink.negotiated_hud()?0:1;
 kombi::pip::corrected_screen::ScreenOutput out={0,0,0,0,wid,style,id};
 unsigned char image[277*160*4];
 for(unsigned y=0;y<160;++y)for(unsigned x=0;x<277;++x){unsigned char*p=image+(y*277+x)*4;bool on=x<4||x>=273||y<4||y>=156||(x>=136&&x<140)||(y>=78&&y<82);p[0]=p[1]=p[2]=on?220:0;p[3]=255;if(x>=10&&x<42&&y>=10&&y<42){p[0]=220;p[1]=180;p[2]=0;}if(x>=235&&x<267&&y>=118&&y<150){p[0]=0;p[1]=110;p[2]=220;}}
 unsigned frame=0;unsigned char metadata[84];supra_pip::MetadataInput mi={8402,1,id,0,style};
 ok=ok&&supra_pip::native_metadata_bgra_framebuffer(metadata,sizeof(metadata),mi);
 if(ok){printf("PIP_BINDING {\"schema\":%u,\"description_id\":%u,\"resource_id\":33554436,\"backing\":[800,480],\"content\":[277,160],\"depth\":0,\"packing\":0,\"screen_format\":8,\"metadata_id_be\":\"%02x%02x%02x%02x\",\"guidance_type\":8402,\"style\":\"%s\",\"destination_flag\":0,\"selection\":%u}\n",hud_candidate?4u:3u,id,metadata[16],metadata[17],metadata[18],metadata[19],argv[3],last_sink);printf("OWNED_WINDOW id=%s run=%s physical_binding_proven=0\n",wid,token);ok=out.inspect(1)&&out.create()&&out.present(image,++frame,false);}
 unsigned long long ready=ms();
 if(ok){snapshot("first-post");puts("PRODUCER_READY");}
 while(ok&&!stopped&&absent(halt)&&absent(go)&&ms()-ready<10000&&ms()-start<13000){ok=quiet()&&sink.pump()&&(sink.negotiated_cluster()||(hud_candidate&&sink.negotiated_hud()));usleep(20000);}
 ok=ok&&!stopped&&absent(halt)&&go_file(go)&&ms()-start<14000;
 unsigned long long visible=ms();if(ok)puts("VISIBLE_WINDOW_STARTED");
 while(ok&&!stopped&&absent(halt)&&ms()-visible<30000&&ms()-start<44000){ok=quiet()&&sink.pump()&&(sink.negotiated_cluster()||(hud_candidate&&sink.negotiated_hud()))&&out.present(image,++frame,false);if(ok){unsigned current=sink.negotiated_hud()?0:1;if(current!=last_sink){printf("SINK_TRANSITION selection=%u elapsed_ms=%llu physical_binding_proven=0\n",current,ms()-visible);last_sink=current;}}usleep(100000);}
 bool full=ok&&!stopped&&ms()-visible>=30000;if(frame)snapshot("before-removal");bool closed=out.close();bool released=sink.close();alarm(0);
 printf("PRODUCER_END frames=%u producer_ok=%u full_visible_window=%u local_cleanup=%u unsubscribe_sent=%u elapsed_ms=%llu\n",frame,unsigned(ok),unsigned(full),unsigned(closed),unsigned(released),ms()-start);
 return full&&closed&&released?0:1;
}
