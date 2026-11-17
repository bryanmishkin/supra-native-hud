// Direct QNX parked runtime. Continuous mode requires explicit admission; no auto-resume.
#include "standalone_wire.hpp"
#include "tach_bitmap.hpp"
#include "navigation_guard.hpp"
#include <pcap.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <errno.h>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <fstream>
using namespace supra;
// Allow scheduling jitter while retaining correlation and 300 ms RPM freshness.
static const unsigned DRAW_ACK_MS=500;
static volatile sig_atomic_t stopped=0;
static void stop(int){stopped=1;}
static uint64_t now(){timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))throw std::runtime_error("clock");return uint64_t(t.tv_sec)*1000+t.tv_nsec/1000000;}
static void fail(const char* s){throw std::runtime_error(s);}
struct Fd {int fd;Fd():fd(-1){}~Fd(){if(fd>=0)close(fd);}private:Fd(const Fd&);Fd& operator=(const Fd&);};
struct Monitor {
 int control,peer;std::string controlPath,input;bool yield;
 pcap_t* capture;unsigned port,ownAddress,clusterAddress;bool foreign,unhealthy;unsigned packets;
 Monitor():control(-1),peer(-1),yield(false),capture(0),port(0),ownAddress(0),clusterAddress(0),foreign(false),unhealthy(false),packets(0){}
 ~Monitor(){if(capture)pcap_close(capture);if(peer>=0)close(peer);if(control>=0)close(control);if(!controlPath.empty())unlink(controlPath.c_str());}
 void listenControl(const char* journal){
  std::string path=std::string(journal)+".handoff";sockaddr_un a;memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(path.size()>=sizeof(a.sun_path))fail("handoff path too long");strcpy(a.sun_path,path.c_str());
  control=socket(AF_UNIX,SOCK_STREAM,0);if(control<0||fcntl(control,F_SETFL,O_NONBLOCK)<0)fail("handoff socket");
  if(bind(control,(sockaddr*)&a,sizeof(a))<0)fail("handoff path already exists/unavailable");controlPath=path;
  if(chmod(path.c_str(),0600)||listen(control,2))fail("handoff listen");
 }
 void finishControl(bool clean){
  if(peer>=0){const char* message=clean?"CLEAN\n":"UNCERTAIN\n";send(peer,message,strlen(message),0);close(peer);peer=-1;}
 }
 void controlPump(){
  if(control<0||yield)return;
  if(peer<0){peer=accept(control,0,0);if(peer>=0&&fcntl(peer,F_SETFL,O_NONBLOCK)<0){close(peer);peer=-1;}}
  if(peer>=0){char buf[16];ssize_t n=recv(peer,buf,sizeof(buf),0);
   if(n>0){input.append(buf,n);if(input=="YIELD1\n")yield=true;else if(input.size()>=7){close(peer);peer=-1;input.clear();}}
   else if(n==0||(n<0&&errno!=EAGAIN&&errno!=EWOULDBLOCK&&errno!=EINTR)){close(peer);peer=-1;input.clear();}
  }
 }
 void open(const char* iface,const char* cluster,unsigned ownPort,unsigned ownIp){
  port=ownPort;ownAddress=ownIp;in_addr target;if(inet_pton(AF_INET,cluster,&target)!=1)fail("cluster address");clusterAddress=ntohl(target.s_addr);
#ifdef SUPRA_TEST
  if(!strcmp(iface,"test-only"))return;
#endif
  char err[PCAP_ERRBUF_SIZE];capture=pcap_open_live(iface,65535,0,10,err);if(!capture)fail("navigation monitor unavailable");
  if(pcap_datalink(capture)!=DLT_EN10MB)fail("unsupported monitor link type");
  // Broad Ethernet filter includes tagged traffic; classify endpoint in bounded code.
  std::string expr="ip or vlan";
  bpf_program f;if(pcap_compile(capture,&f,expr.c_str(),1,0xffffffff)<0)fail("monitor filter");int r=pcap_setfilter(capture,&f);pcap_freecode(&f);if(r<0||pcap_setnonblock(capture,1,err)<0)fail("monitor setup");
 }
 void pump(){
  controlPump();
#ifdef SUPRA_TEST
  const char* trigger=getenv("SUPRA_TEST_FACTORY_TRIGGER");if(trigger&&access(trigger,F_OK)==0)foreign=true;
  const char* loss=getenv("SUPRA_TEST_MONITOR_LOSS");if(loss&&access(loss,F_OK)==0)unhealthy=true;
#endif
  if(!capture)return;
  for(unsigned i=0;i<256;++i){pcap_pkthdr* h;const u_char* b;int r=pcap_next_ex(capture,&h,&b);if(r==0)break;if(r<0){fprintf(stderr,"monitor read: %s\n",pcap_geterr(capture));unhealthy=true;break;}++packets;
   Traffic t=classifyTraffic(b,h->caplen,h->len,ownAddress,port,clusterAddress);
   if(t==UnknownTraffic){fprintf(stderr,"monitor unknown packet cap=%u wire=%u\n",(unsigned)h->caplen,(unsigned)h->len);unhealthy=true;break;}
   if(t==FactoryTraffic)foreign=true;
   if(i==255)unhealthy=true;
  }
  pcap_stat stats;memset(&stats,0,sizeof(stats));int status=pcap_stats(capture,&stats);if(status<0||stats.ps_drop||stats.ps_ifdrop){fprintf(stderr,"monitor stats status=%d drop=%u ifdrop=%u error=%s\n",status,stats.ps_drop,stats.ps_ifdrop,pcap_geterr(capture));unhealthy=true;}
 }
 void guard(){pump();if(foreign)fail("factory_activity_quiesced");if(unhealthy)fail("monitor_unknown_quiesced");}
};
static void ready(int fd,bool write,uint64_t deadline,Monitor* m){
 for(;;){if(m)m->guard();uint64_t t=now();if(t>=deadline)fail("I/O deadline");unsigned ms=(unsigned)(deadline-t);if(ms>10)ms=10;timeval tv;tv.tv_sec=0;tv.tv_usec=ms*1000;fd_set set;FD_ZERO(&set);FD_SET(fd,&set);int r=select(fd+1,write?0:&set,write?&set:0,0,&tv);if(r>0)return;if(r<0&&errno!=EINTR)fail("select");}
}
static void connectTo(Fd& s,const char* address,unsigned port,const char* local,uint64_t deadline){
 s.fd=socket(AF_INET,SOCK_STREAM,0);if(s.fd<0||fcntl(s.fd,F_SETFL,O_NONBLOCK)<0)fail("socket");
 sockaddr_in a;memset(&a,0,sizeof(a));a.sin_family=AF_INET;if(local){if(inet_pton(AF_INET,local,&a.sin_addr)!=1||bind(s.fd,(sockaddr*)&a,sizeof(a)))fail("local bind");}
 a.sin_port=htons(port);if(inet_pton(AF_INET,address,&a.sin_addr)!=1)fail("IPv4 address");
 if(connect(s.fd,(sockaddr*)&a,sizeof(a))<0){if(errno!=EINPROGRESS)fail("connect");ready(s.fd,true,deadline,0);int e=0;socklen_t n=sizeof(e);if(getsockopt(s.fd,SOL_SOCKET,SO_ERROR,&e,&n)||e)fail("connect completion");}
}
static void sendBytes(int fd,const Bytes& b,uint64_t deadline,Monitor* m){unsigned at=0;while(at<b.size()){ready(fd,true,deadline,m);if(m)m->guard();ssize_t n=send(fd,&b[at],b.size()-at,0);if(n>0)at+=n;else if(n==0||(errno!=EINTR&&errno!=EAGAIN&&errno!=EWOULDBLOCK))fail("send");}}
static Bytes receive(int fd,unsigned count,uint64_t deadline,Monitor* m){if(count>65552)fail("read bound");Bytes b(count);unsigned at=0;while(at<count){ready(fd,false,deadline,m);ssize_t n=recv(fd,&b[at],count-at,0);if(n>0)at+=n;else if(n==0||(errno!=EINTR&&errno!=EAGAIN&&errno!=EWOULDBLOCK))fail("receive");}return b;}
struct Ric {
 Fd connection;Monitor monitor;unsigned sequence;bool uncertain,cleaning;FILE* log;
 Ric():sequence(0),uncertain(false),cleaning(false),log(0){
#ifdef SUPRA_TEST
 const char* start=getenv("SUPRA_TEST_SEQUENCE_START");if(start)sequence=(unsigned)strtoul(start,0,10);
#endif
 }
 ~Ric(){if(log)fclose(log);}
 Bytes call(unsigned method,const Bytes& body,unsigned timeout){
  if(uncertain)fail("transport uncertain; no reconnect");monitor.guard();if(sequence==65535)sequence=0;unsigned seq=++sequence;uint64_t deadline=now()+timeout;
  try{Bytes tx=request(method,seq,body);if(log && ftell(log)>1048576){if(fflush(log)||ftruncate(fileno(log),0))fail("journal rotation");rewind(log);}if(log){fprintf(log,"{\"request\":%u,\"method\":%u,\"bytes\":%lu}\n",seq,method,(unsigned long)tx.size());fflush(log);}sendBytes(connection.fd,tx,deadline,&monitor);
   for(unsigned i=0;i<9;++i){Bytes h=receive(connection.fd,16,deadline,&monitor);unsigned n=read32(h,4);if(n<8||n>65544)fail("SOME/IP length");
    if(read32(h,0)==0xffff8000&&n==8&&read32(h,8)==0xdeadbeef&&h[12]==1&&h[13]==1&&(h[14]==2||h[14]==128)&&h[15]==0)continue;
    Bytes tail=receive(connection.fd,n-8,deadline,&monitor);h.insert(h.end(),tail.begin(),tail.end());Bytes result=response(method,seq,h);if(log){fprintf(log,"{\"ack\":%u}\n",seq);fflush(log);}return result;
   }fail("cookie bound");
  }catch(...){uncertain=true;throw;}return Bytes();
 }
 void empty(unsigned m,const Bytes& b,unsigned timeout){if(!call(m,b,timeout).empty()){uncertain=true;fail("nonempty ack");}}
 bool check(unsigned id,unsigned timeout){Bytes b=call(2,checkBody(id),timeout);if(b.size()!=1||b[0]>1){uncertain=true;fail("invalid presence");}return b[0]!=0;}
};
static double rpmSampleRaw(const char* local,const char* gateway,uint64_t& stamp,Monitor& monitor){
 stamp=now();uint64_t deadline=stamp+200;Fd socket;connectTo(socket,gateway,6801,local,deadline);Bytes q;put32(q,4);q.push_back(0);q.push_back(1);q.push_back(0xf4);q.push_back(0x12);q.push_back(1);q.push_back(0x0c);sendBytes(socket.fd,q,deadline,&monitor);
 for(unsigned i=0;i<24;++i){Bytes h=receive(socket.fd,6,deadline,&monitor);unsigned n=read32(h,0),kind=(h[4]<<8)|h[5];if(n<2||n>8192)fail("RPM frame length");Bytes b=receive(socket.fd,n,deadline,&monitor);
  if(kind==0x12){Bytes ack;put32(ack,2);ack.push_back(0);ack.push_back(0x13);ack.push_back(0);ack.push_back(0xf4);sendBytes(socket.fd,ack,deadline,&monitor);}
  if(kind!=1||b[0]!=0x12||b[1]!=0xf4)continue;
  if(n==5&&b[2]==0x7f&&b[3]==1&&b[4]==0x78)continue;
  if(n!=6||b[2]!=0x41||b[3]!=0x0c)fail("RPM reply");return ((b[4]<<8)|b[5])/4.0;
 }fail("RPM frame limit");return 0;
}
static double rpmSample(const char* local,const char* gateway,uint64_t& stamp,Monitor& monitor){
 try{return rpmSampleRaw(local,gateway,stamp,monitor);}catch(const std::exception& e){
  if(!strcmp(e.what(),"I/O deadline")||!strcmp(e.what(),"send")||!strcmp(e.what(),"receive")||!strcmp(e.what(),"connect")||!strcmp(e.what(),"connect completion")||!strcmp(e.what(),"local bind")||!strcmp(e.what(),"RPM frame length")||!strcmp(e.what(),"RPM reply")||!strcmp(e.what(),"RPM frame limit")){
   int saved=errno;fprintf(stderr,"RPM transport: %s errno=%d (%s) elapsed_ms=%llu\n",e.what(),saved,strerror(saved),(unsigned long long)(now()-stamp));
   throw std::runtime_error(std::string("rpm_transport:")+e.what());
  }throw;
 }
}
static Bytes frame(double rpm,uint64_t stamp){Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;in.rpm.valid=true;in.rpm.value=rpm;in.rpm.at=stamp;HudCore core(c);Update u=core.update(in,now());if(u.action!=Present)fail("invalid/stale RPM");return encodeRle(tachBitmapSport(u.frame),true);}
static bool disabled(){const char* p=getenv("SUPRA_HUD_DISABLE_FILE");return p&&*p&&access(p,F_OK)==0;}
static void heartbeatCheck(){
 const char* path=getenv("SUPRA_HUD_HEARTBEAT");if(!path||!*path)return;
 FILE* f=fopen(path,"r");unsigned long long t=0;int n=f?fscanf(f,"%llu",&t):0;if(f)fclose(f);
 uint64_t current=now();if(n!=1||current<t||current-t>1500)fail("supervisor heartbeat lost");
}
static void acquireAdmission(Monitor& monitor){
 const char* path=getenv("SUPRA_HUD_BROKER_SOCKET");if(!path||!*path)return;
 sockaddr_un a;memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(strlen(path)>=sizeof(a.sun_path))fail("admission path");strcpy(a.sun_path,path);
 Fd fd;fd.fd=socket(AF_UNIX,SOCK_STREAM,0);if(fd.fd<0||fcntl(fd.fd,F_SETFL,O_NONBLOCK))fail("admission unavailable");
 int connected=connect(fd.fd,(sockaddr*)&a,sizeof(a));if(connected<0&&errno!=EINPROGRESS)fail("admission unavailable");
 if(connected<0){uint64_t deadline=now()+1000;bool ready=false;while(now()<deadline){monitor.controlPump();if(monitor.yield)fail("factory_navigation_request");fd_set w;FD_ZERO(&w);FD_SET(fd.fd,&w);timeval t;t.tv_sec=0;t.tv_usec=1000;if(select(fd.fd+1,0,&w,0,&t)>0){int error=0;socklen_t len=sizeof(error);if(getsockopt(fd.fd,SOL_SOCKET,SO_ERROR,&error,&len)||error)fail("admission unavailable");ready=true;break;}}if(!ready)fail("admission unavailable");}
 unsigned char request[14]={'A','C','Q','U','I','R','E','1',0,0,0,0,0,0};for(unsigned i=0;i<4;++i)request[8+i]=(monitor.ownAddress>>(24-8*i))&255;request[12]=monitor.port>>8;request[13]=monitor.port&255;
 if(send(fd.fd,request,sizeof(request),0)!=(ssize_t)sizeof(request))fail("admission request");
 char reply[8];unsigned at=0;uint64_t end=now()+1000;
 while(now()<end&&at<sizeof(reply)){monitor.controlPump();if(monitor.yield)fail("factory_navigation_request");ssize_t n=recv(fd.fd,reply+at,sizeof(reply)-at,0);if(n>0){at+=n;if(at==3&&!memcmp(reply,"GO\n",3))return;if(at>=5)break;}else if(n==0)break;else if(errno!=EAGAIN&&errno!=EINTR)break;usleep(1000);}
 fail("admission_denied");
}
static void checkpoint(Ric& r){heartbeatCheck();r.monitor.guard();if(disabled())fail("disabled");if(r.monitor.yield)fail("factory_navigation_request");if(stopped)fail("signal");}
static void fresh(uint64_t stamp){if(now()<stamp||now()-stamp>300)fail("RPM stale");}
int main(int argc,char** argv){
 if(argc==2 && !strcmp(argv[1],"--self-check")){
  try{Bytes raw(21600,0);for(unsigned i=3;i<raw.size();i+=4)raw[i]=255;Bytes image=encodeRle(raw,true);if(image.empty())return 2;puts("{\"self_check\":true,\"vehicle_io\":false}");return 0;}catch(...){return 2;}
 }
 if(argc==4 && !strcmp(argv[1],"--probe-rpm")){
  signal(SIGPIPE,SIG_IGN);Monitor monitor;unsigned valid=0;
  try{for(unsigned i=0;i<40;++i){uint64_t stamp;double rpm=rpmSample(argv[2],argv[3],stamp,monitor);fresh(stamp);if(!(rpm>=0&&rpm<=7700))fail("RPM outside display bounds");++valid;printf("{\"rpm\":%.2f,\"sample_ms\":%llu,\"latency_ms\":%llu}\n",rpm,(unsigned long long)stamp,(unsigned long long)(now()-stamp));fflush(stdout);while(now()<stamp+250)usleep(5000);}printf("{\"rpm_probe_passed\":true,\"valid\":%u,\"hud_writes\":0}\n",valid);return 0;}catch(const std::exception& e){fprintf(stderr,"RPM probe failed: %s\n",e.what());return 2;}
 }

 bool continuous=argc==9&&!strcmp(argv[1],"--continuous-parked-guidance-stopped");
 if(argc!=9 || (!continuous && strcmp(argv[1],"--parked-guidance-stopped"))){fprintf(stderr,"No connections made. Parked candidate only:\n%s --parked-guidance-stopped PROFILE LOCAL_IP GATEWAY_IP CLUSTER_IP MONITOR_INTERFACE SECONDS NEW_JOURNAL\nNo autostart; navigation activity stops writes without canceling factory state.\n",argv[0]);return 64;}
 char* end=0;long seconds=strtol(argv[7],&end,10);if(!end||*end||(continuous?seconds!=0:(seconds<1||seconds>30)))return 64;
 signal(SIGINT,stop);signal(SIGTERM,stop);signal(SIGPIPE,SIG_IGN);Ric ric;Profile profile;bool graph=false,owned[2]={false,false},clean=true;unsigned visible=0x01000009,frames=0;std::string reason="duration_complete";
 try{
  if(disabled())fail("disabled");profile=readProfile(argv[2]);int logfd=::open(argv[8],O_WRONLY|O_CREAT|O_EXCL,0600);if(logfd<0)fail("new journal required");ric.log=fdopen(logfd,"w");if(!ric.log){close(logfd);fail("journal");}
  #ifdef SUPRA_TEST
  const char* beforeControl=getenv("SUPRA_TEST_BEFORE_CONTROL_US");if(beforeControl)usleep((unsigned)strtoul(beforeControl,0,10));
#endif
  ric.monitor.listenControl(argv[8]);
  connectTo(ric.connection,argv[5],30502,0,now()+2000);sockaddr_in address;socklen_t len=sizeof(address);if(getsockname(ric.connection.fd,(sockaddr*)&address,&len))fail("local port");ric.monitor.open(argv[6],argv[5],ntohs(address.sin_port),ntohl(address.sin_addr.s_addr));
  acquireAdmission(ric.monitor);heartbeatCheck();
  for(unsigned id=0x01000000;id<=0x01000009;++id)if(ric.check(id,2000))fail("bitmap pool in use");
  uint64_t stamp;double rpm=rpmSample(argv[3],argv[4],stamp,ric.monitor);Bytes image=frame(rpm,stamp);checkpoint(ric);owned[1]=true;ric.empty(3,bitmapBody(visible,image),DRAW_ACK_MS);if(!ric.check(visible,DRAW_ACK_MS))fail("upload absent");fresh(stamp);
  for(unsigned i=0;i<profile.setup.size();++i){fresh(stamp);checkpoint(ric);graph=true;ric.empty(profile.setup[i].method,profile.setup[i].body,DRAW_ACK_MS);}++frames;
  uint64_t deadline=continuous?~uint64_t(0):now()+seconds*1000;
  while(!stopped&&!disabled()&&!ric.monitor.yield&&now()<deadline){
   unsigned next=visible==0x01000009?0x01000008:0x01000009;rpm=rpmSample(argv[3],argv[4],stamp,ric.monitor);image=frame(rpm,stamp);fresh(stamp);checkpoint(ric);if(ric.check(next,DRAW_ACK_MS))fail("next bitmap in use");checkpoint(ric);owned[next-0x01000008]=true;ric.empty(3,bitmapBody(next,image),DRAW_ACK_MS);if(!ric.check(next,DRAW_ACK_MS))fail("upload absent");fresh(stamp);checkpoint(ric);
   Bytes road=profile.setup[4].body;set32(road,32,next);ric.empty(14,road,DRAW_ACK_MS);fresh(stamp);ric.empty(8,removeBody(visible),DRAW_ACK_MS);if(ric.check(visible,DRAW_ACK_MS))fail("old image retained");owned[visible-0x01000008]=false;visible=next;++frames;
   if(ric.log){fprintf(ric.log,"{\"rpm\":%.2f,\"sample_ms\":%llu,\"frame\":%u}\n",rpm,(unsigned long long)stamp,frames);fflush(ric.log);}
   while(!stopped&&!disabled()&&!ric.monitor.yield&&now()<deadline&&now()<stamp+250){ric.monitor.guard();usleep(5000);}
  }
  if(disabled())reason="disabled";else if(stopped)reason="signal";else if(ric.monitor.yield)reason="factory_navigation_request";
 }catch(const std::exception& e){reason=e.what();}
 // Passive detection is revocation, not permission to cancel shared factory models.
 // Never send state5/state0 after foreign activity, capture loss or uncertain I/O.
 try{ric.monitor.pump();}catch(...){ric.monitor.unhealthy=true;}
 if(ric.uncertain||ric.monitor.foreign||ric.monitor.unhealthy){clean=!graph&&!owned[0]&&!owned[1];}
 else{
  ric.cleaning=true;
  if(graph){for(unsigned i=0;i<profile.cleanup.size();++i){try{ric.empty(profile.cleanup[i].method,profile.cleanup[i].body,2000);}catch(...){clean=false;break;}}}
  if(clean)for(unsigned i=0;i<2;++i)if(owned[i]){try{unsigned id=0x01000008+i;ric.empty(8,removeBody(id),2000);if(ric.check(id,2000))fail("cleanup image retained");owned[i]=false;}catch(...){clean=false;break;}}
 }
 if(owned[0]||owned[1])clean=false;
 ric.monitor.finishControl(clean);
#ifdef SUPRA_TEST
 const char* exitDelay=getenv("SUPRA_TEST_EXIT_DELAY_US");if(exitDelay&&clean){unlink(ric.monitor.controlPath.c_str());usleep((unsigned)strtoul(exitDelay,0,10));}
#endif
 fprintf(stdout,"{\"reason\":\"%s\",\"frames\":%u,\"cleanup_verified\":%s,\"factory_activity\":%s,\"monitor_unknown\":%s,\"automatic_resume\":false,\"shared_instance_preserved\":true}\n",reason.c_str(),frames,clean?"true":"false",ric.monitor.foreign?"true":"false",ric.monitor.unhealthy?"true":"false");
 return clean&&(reason=="duration_complete"||reason=="signal"||reason=="factory_navigation_request"||reason=="disabled")?0:2;
}
