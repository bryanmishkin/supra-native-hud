// Persistent supervisor. Factory events, not a duration/quiet timer, control resume.
#define main supra_parked_entry
#include "supra_standalone.cpp"
#undef main
#include "factory_lease.hpp"
#include "factory_stream.hpp"
#include <sys/wait.h>
#include <vector>
static int unixConnect(const std::string& path){
 sockaddr_un a;memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(path.size()>=sizeof(a.sun_path))return -1;strcpy(a.sun_path,path.c_str());
 int fd=socket(AF_UNIX,SOCK_STREAM,0);if(fd<0)return -1;
 timeval t;t.tv_sec=0;t.tv_usec=250000;setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&t,sizeof(t));setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&t,sizeof(t));
 if(connect(fd,(sockaddr*)&a,sizeof(a))){close(fd);return -1;}return fd;
}
static bool controlStop(const std::string& path){int fd=unixConnect(path);if(fd<0)return false;bool ok=send(fd,"YIELD1\n",7,0)==7;char b[6];unsigned at=0;uint64_t end=now()+2500;while(ok&&at<6&&now()<end){ssize_t n=recv(fd,b+at,6-at,0);if(n>0)at+=n;else if(n<0&&(errno==EAGAIN||errno==EINTR))continue;else break;}close(fd);return ok&&at==6&&!memcmp(b,"CLEAN\n",6);}
static bool readAll(int fd,unsigned char* data,unsigned n,unsigned timeout=300){unsigned at=0;uint64_t end=now()+timeout;while(at<n&&now()<end){ssize_t got=recv(fd,data+at,n-at,0);if(got>0)at+=got;else if(got<0&&(errno==EINTR||errno==EAGAIN))continue;else return false;}return at==n;}
static void replyText(int fd,const char* s){ssize_t n=send(fd,s,strlen(s),0);(void)n;}
static bool privateDir(const std::string& p){struct stat s;return !lstat(p.c_str(),&s)&&S_ISDIR(s.st_mode)&&s.st_uid==geteuid()&&!(s.st_mode&0022);}
static void saveText(const std::string& path,const std::string& body){std::string temp=path+".new";int fd=open(temp.c_str(),O_WRONLY|O_CREAT|O_TRUNC,0600);if(fd<0)fail("state write");bool ok=write(fd,body.data(),body.size())==(ssize_t)body.size();close(fd);if(!ok||rename(temp.c_str(),path.c_str()))fail("state replace");}
struct Resident {
 FactoryLease lease;FactoryStream stream;pcap_t* cap;FILE* bootTrace;unsigned traceBytes;int server;pid_t child;std::string root,state,socketPath;bool quit,cleanAck,admitted,cleanupProven;unsigned starts,cleanStops,lastGeneration,ioRetries;uint64_t started,lastStatus,bootTime,lastFactory,retryAfter;
 Resident(const char* r,const char* s):stream(lease),cap(0),bootTrace(0),traceBytes(0),server(-1),child(0),root(r),state(s),quit(false),cleanAck(false),admitted(false),cleanupProven(true),starts(0),cleanStops(0),lastGeneration(0),ioRetries(0),started(0),lastStatus(0),bootTime(now()),lastFactory(now()),retryAfter(0){}
 ~Resident(){if(bootTrace)fclose(bootTrace);if(cap)pcap_close(cap);if(server>=0)close(server);if(!socketPath.empty())unlink(socketPath.c_str());}
 void capture(const char* iface){
 bootTrace=fopen((state+"/startup.pcap").c_str(),"wb");if(!bootTrace)fail("startup trace");
 const uint32_t header[]={0xa1b2c3d4,0x00040002,0,0,65535,1};if(fwrite(header,1,24,bootTrace)!=24)fail("startup trace header");
#ifdef SUPRA_TEST
 if(!strcmp(iface,"test-only"))return;
#endif
 char err[PCAP_ERRBUF_SIZE];cap=pcap_open_live(iface,65535,0,10,err);if(!cap||pcap_datalink(cap)!=DLT_EN10MB)fail("factory capture unavailable");bpf_program f;if(pcap_compile(cap,&f,"ip or vlan",1,0xffffffff)<0)fail("factory capture filter");int rc=pcap_setfilter(cap,&f);pcap_freecode(&f);if(rc||pcap_setnonblock(cap,1,err))fail("factory capture nonblock");if(fcntl(pcap_fileno(cap),F_SETFD,FD_CLOEXEC))fail("capture close-on-exec");}
 void pump(){if(!cap)return;for(unsigned i=0;i<2048;++i){pcap_pkthdr* h;const u_char* b;int rc=pcap_next_ex(cap,&h,&b);if(!rc)break;if(rc<0){lease.fault("capture read");break;}if(traceBytes+h->caplen+16<=2097152){uint32_t record[4]={(uint32_t)h->ts.tv_sec,(uint32_t)h->ts.tv_usec,h->caplen,h->len};fwrite(record,1,16,bootTrace);fwrite(b,1,h->caplen,bootTrace);traceBytes+=h->caplen+16;fflush(bootTrace);}stream.ethernet(b,h->caplen,h->len);if(lease.failed())break;if(i==2047)lease.fault("capture backlog");}pcap_stat st;memset(&st,0,sizeof(st));if(pcap_stats(cap,&st)||st.ps_drop||st.ps_ifdrop)lease.fault("capture loss");}
 void bindServer(){socketPath=state+"/factory.sock";sockaddr_un a;memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(socketPath.size()>=sizeof(a.sun_path))fail("broker path");strcpy(a.sun_path,socketPath.c_str());server=socket(AF_UNIX,SOCK_STREAM,0);if(server<0||bind(server,(sockaddr*)&a,sizeof(a))||chmod(socketPath.c_str(),0600)||listen(server,16)||fcntl(server,F_SETFL,O_NONBLOCK))fail("broker bind");}
 void heartbeat(){char b[64];snprintf(b,sizeof(b),"%llu\n",(unsigned long long)now());saveText(state+"/heartbeat",b);}
 void reap(){if(!child)return;int status=0;pid_t got=waitpid(child,&status,WNOHANG);if(got<=0)return;child=0;std::ifstream f((state+"/worker.result").c_str());std::string text((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());
  bool clean=text.find("\"cleanup_verified\":true")!=std::string::npos;
  cleanupProven=WIFEXITED(status)&&clean;
  bool expected=text.find("\"reason\":\"factory_navigation_request\"")!=std::string::npos||text.find("\"reason\":\"admission_denied\"")!=std::string::npos||text.find("\"reason\":\"disabled\"")!=std::string::npos;
  bool retryable=WIFEXITED(status)&&clean&&(text.find("\"reason\":\"rpm_transport:")!=std::string::npos||text.find("\"reason\":\"RPM stale\"")!=std::string::npos);
  if(retryable){if(now()-started>=30000)ioRetries=0;if(++ioRetries<=3)retryAfter=now()+1000*(1U<<(ioRetries-1));else lease.fault("clean I/O retry budget exhausted");}
  else if(!WIFEXITED(status)||!clean||!expected)lease.fault("worker exit/cleanup uncertain");
  saveText(state+"/last-result",text);
 }
 bool stop(){if(!child||cleanAck)return true;if(!admitted){cleanAck=true;++cleanStops;return true;}bool ok=controlStop(state+"/active.jsonl.handoff");if(!ok)lease.fault("worker handoff not CLEAN");cleanAck=ok;if(ok)++cleanStops;return ok;}
 void spawn(){
  if(child||!lease.available()||quit||now()<retryAfter||now()-lastFactory<200)return;
#ifndef SUPRA_TEST
  // Additional boot readiness delay; never grants ownership or assumes idle.
  if(now()-bootTime<30000)return;
#endif
  // Previous process must have exited; archive its latest bounded journal.
  if(!access((state+"/active.jsonl.handoff").c_str(),F_OK)){lease.fault("stale worker socket");return;}
  rename((state+"/active.jsonl").c_str(),(state+"/previous.jsonl").c_str());
  pid_t p=fork();if(p<0){lease.fault("worker fork");return;}
  if(!p){close(server);int result=open((state+"/worker.result").c_str(),O_WRONLY|O_CREAT|O_TRUNC,0600);int error=open((state+"/worker.stderr").c_str(),O_WRONLY|O_CREAT|O_TRUNC,0600);if(result<0||error<0)_exit(126);dup2(result,1);dup2(error,2);close(result);close(error);
   setenv("SUPRA_HUD_BROKER_SOCKET",socketPath.c_str(),1);setenv("SUPRA_HUD_HEARTBEAT",(state+"/heartbeat").c_str(),1);setenv("SUPRA_HUD_DISABLE_FILE",(root+"/disabled").c_str(),1);
   std::string exe=root+"/supra-standalone-parked-qnx",profile=root+"/supra-profile.bin",journal=state+"/active.jsonl";
#ifdef SUPRA_TEST
   const char* local="127.0.0.1";const char* gateway=local;const char* cluster=local;const char* iface="test-only";
#else
   const char* local="169.254.199.119";const char* gateway="169.254.106.96";const char* cluster="160.48.199.96";const char* iface="vlan73";
#endif
   execl(exe.c_str(),exe.c_str(),"--continuous-parked-guidance-stopped",profile.c_str(),local,gateway,cluster,iface,"0",journal.c_str(),(char*)0);_exit(127);
  }
  child=p;cleanAck=false;admitted=false;cleanupProven=false;started=now();++starts;char count[32];snprintf(count,sizeof(count),"%u\n",starts);saveText(state+"/worker.starts",count);
 }
 void acceptOne(){int fd=accept(server,0,0);if(fd<0)return;timeval timeout;timeout.tv_sec=0;timeout.tv_usec=50000;setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));unsigned char h[8];
  if(!readAll(fd,h,8)){close(fd);return;}
#ifdef SUPRA_TEST
  if(!memcmp(h,"TESTCLS1",8)){lease.fault("factory transport closed");replyText(fd,"OK\n");close(fd);return;}
  if(!memcmp(h,"TESTREQ1",8)||!memcmp(h,"TESTACK1",8)){
   unsigned char size[4];if(!readAll(fd,size,4)){close(fd);return;}unsigned n=(unsigned(size[0])<<24)|(unsigned(size[1])<<16)|(unsigned(size[2])<<8)|size[3];
   if(n<16||n>65552){close(fd);return;}FactoryLease::Packet packet(n);if(!readAll(fd,&packet[0],n)){close(fd);return;}
   bool ok=h[4]=='R'?lease.outgoing(packet):lease.reply(packet);replyText(fd,ok?"OK\n":"ERROR\n");close(fd);return;
  }
#endif
  if(!memcmp(h,"ACQUIRE1",8)){unsigned char own[6];if(!readAll(fd,own,6)){close(fd);return;}unsigned ip=(unsigned(own[0])<<24)|(unsigned(own[1])<<16)|(unsigned(own[2])<<8)|own[3];unsigned port=unsigned(own[4])*256+own[5];if(!port){close(fd);return;}stream.registerOwn(ip,port);pump();bool grant=child&&lease.available()&&!quit&&!cleanAck;if(grant)admitted=true;replyText(fd,grant?"GO\n":"WAIT\n");close(fd);return;}
  if(!memcmp(h,"STOPAPP1",8)){quit=true;replyText(fd,stop()?"CLEAN\n":"UNCERTAIN\n");close(fd);return;}
  if(memcmp(h,"PRE1",4)||h[4]>1||h[5]||h[6]||h[7]){lease.fault("broker event header");stop();close(fd);return;}
  unsigned char size[4];if(!readAll(fd,size,4)){lease.fault("broker event length");stop();close(fd);return;}unsigned n=(unsigned(size[0])<<24)|(unsigned(size[1])<<16)|(unsigned(size[2])<<8)|size[3];
  if(n<16||n>65552){lease.fault("broker event bound");stop();close(fd);return;}FactoryLease::Packet packet(n);if(!readAll(fd,&packet[0],n)){lease.fault("broker event truncation");stop();close(fd);return;}
  bool tracked=lease.before(packet,h[4]);bool clean=stop();replyText(fd,tracked&&clean?"CLEAN\n":"UNCERTAIN\n");close(fd);
 }
 void status(){
  if(now()-lastStatus<1000)return;lastStatus=now();char b[512];snprintf(b,sizeof(b),"{\"uptime_ms\":%llu,\"worker_starts\":%u,\"worker_running\":%s,\"clean_stops\":%u,\"navigation_idle_commits\":%u,\"navigation_active_commits\":%u,\"radio_idle_commits\":%u,\"radio_active_commits\":%u,\"available\":%s,\"quarantined\":%s}\n",(unsigned long long)(now()-bootTime),starts,child?"true":"false",cleanStops,lease.idleCommits[0],lease.activeCommits[0],lease.idleCommits[1],lease.activeCommits[1],lease.available()?"true":"false",lease.failed()?"true":"false");saveText(state+"/acceptance.json",b);char admission[160];snprintf(admission,sizeof(admission),"{\"navigation_state\":%u,\"radio_state\":%u,\"pending_requests\":%u,\"cleanup_proven\":%s}\n",unsigned(lease.state(0)),unsigned(lease.state(1)),lease.pendingCount(),cleanupProven?"true":"false");saveText(state+"/admission.json",admission);
 }
 void loop(){
  while(!stopped&&!quit){heartbeat();pump();acceptOne();reap();status();if(lastGeneration!=lease.generation()){lastGeneration=lease.generation();lastFactory=now();}if(!access((root+"/disabled").c_str(),F_OK))quit=true;
   if(lease.failed()){stop();quit=true;}else spawn();
   // A child must reach the admission socket promptly; no blind restart loop.
   if(child&&!cleanAck&&now()-started>3000&&access((state+"/active.jsonl.handoff").c_str(),F_OK))lease.fault("worker startup deadline");
   usleep(10000);
  }
  stop();uint64_t deadline=now()+3000;while(child&&now()<deadline){reap();usleep(10000);}
  if(child)lease.fault("worker did not exit");
  lastStatus=0;status();
  // Engine telemetry and factory TCP can disappear during shutdown. These two
  // reasons are boot-local only with no child and proven clean withdrawal.
  // Every other fault retains the existing persistent quarantine behavior.
  bool bootOnly=lease.failed()&&(lease.reason()=="clean I/O retry budget exhausted"||lease.reason()=="factory transport closed")&&!child&&cleanupProven;
  if(lease.failed()&&!bootOnly)saveText(root+"/disabled",lease.reason()+"\n");
  std::string terminal=lease.failed()?std::string(bootOnly?"BOOT_INHIBITED: ":"QUARANTINED: ")+lease.reason()+"\n":"STOPPED\n";
  saveText(state+"/resident.status",terminal);
  saveText(root+"/last-resident.status",terminal+std::string("cleanup_proven=")+(cleanupProven?"true\n":"false\n"));
 }
};
int main(int argc,char** argv){
 if(argc==2&&!strcmp(argv[1],"--sync-state")){sync();puts("STATE_SYNCED");return 0;}
 if(argc==3&&!strcmp(argv[1],"--stop")){signal(SIGPIPE,SIG_IGN);int fd=unixConnect(std::string(argv[2])+"/factory.sock");if(fd<0)return 2;replyText(fd,"STOPAPP1");char b[6];bool ok=readAll(fd,(unsigned char*)b,6,3000)&&!memcmp(b,"CLEAN\n",6);close(fd);if(ok)puts("CLEAN");return ok?0:2;}
 if(argc!=4){fprintf(stderr,"usage: supra-resident ROOT RAM_STATE INTERFACE\n");return 64;}
 signal(SIGPIPE,SIG_IGN);signal(SIGINT,stop);signal(SIGTERM,stop);umask(077);
 try{std::string root=argv[1],state=argv[2];if(!privateDir(root)||(!access((root+"/disabled").c_str(),F_OK)))fail("disabled/insecure release root");if(mkdir(state.c_str(),0700)&&errno!=EEXIST)fail("state directory");if(!privateDir(state))fail("insecure state directory");
  int lock=open((state+"/resident.lock").c_str(),O_WRONLY|O_CREAT|O_EXCL,0600);if(lock<0)fail("existing resident or unresolved state");close(lock);
  Resident r(argv[1],argv[2]);r.capture(argv[3]);r.bindServer();r.heartbeat();saveText(state+"/ready","CAPTURE_READY\n");r.loop();return r.lease.failed()?2:0;
 }catch(const std::exception& e){fprintf(stderr,"resident: %s\n",e.what());try{if(privateDir(argv[1]))saveText(std::string(argv[1])+"/last-resident.status",std::string("STARTUP_OR_RUNTIME_EXCEPTION: ")+e.what()+"\n");}catch(...){}return 2;}
}
