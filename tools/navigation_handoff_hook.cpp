// Experimental pre-send interposer. NEVER install/preload without target validation.
// Filters exact cluster endpoint and defers factory sending for a bounded handoff.
#include <dlfcn.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdio.h>
#include <pthread.h>
static pthread_mutex_t mutex=PTHREAD_MUTEX_INITIALIZER;
static const char* adapter="_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERK8TWeakPtrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE";
typedef int (*Sender)(void*,const void*,void*);
typedef unsigned (*Length)(void*);
typedef unsigned char* (*Data)(void*);
typedef sockaddr* (*Address)(void*);
static long long ms(){timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return -1;return (long long)t.tv_sec*1000+t.tv_nsec/1000000;}
static void traceEvent(const char* event){
 const char* path=getenv("SUPRA_HUD_TRACE_FILE");
 if(!path||!*path)return;
 struct stat st;if(!lstat(path,&st)&&(!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||st.st_size>65536))return;
 int flags=O_WRONLY|O_APPEND|O_CREAT;
#ifdef O_NOFOLLOW
 flags|=O_NOFOLLOW;
#endif
 int fd=open(path,flags,0600);if(fd<0)return;
 char line[160];int n=snprintf(line,sizeof(line),"%lld pid=%ld %s\n",ms(),(long)getpid(),event);
 if(n>0&&n<(int)sizeof(line)){ssize_t written=write(fd,line,(size_t)n);(void)written;}
 close(fd);
}
static bool waitFd(int fd,bool write,long long until){for(;;){long long current=ms();if(current<0)return false;long long left=until-current;if(left<=0||left>3000)return false;timeval tv;tv.tv_sec=left/1000;tv.tv_usec=(left%1000)*1000;fd_set s;FD_ZERO(&s);FD_SET(fd,&s);int r=select(fd+1,write?0:&s,write?&s:0,0,&tv);if(r>0)return true;if(r<0&&errno!=EINTR)return false;}}
static void handoff(const char* path){
 sockaddr_un a;memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(strlen(path)>=sizeof(a.sun_path))return;strcpy(a.sun_path,path);
 int fd=socket(AF_UNIX,SOCK_STREAM,0);if(fd<0)return;
#ifndef MSG_NOSIGNAL
#ifdef SO_NOSIGPIPE
 int noPipe=1;if(setsockopt(fd,SOL_SOCKET,SO_NOSIGPIPE,&noPipe,sizeof(noPipe))){close(fd);return;}
#else
 close(fd);return; // Never alter the factory process signal disposition.
#endif
#endif
if(fcntl(fd,F_SETFL,O_NONBLOCK)<0){close(fd);return;}
 long long start=ms();if(start<0){close(fd);return;}long long deadline=start+3000;
 int r=connect(fd,(sockaddr*)&a,sizeof(a));
 if(r<0&&errno!=EINPROGRESS){close(fd);return;} // No active runtime: leave factory untouched.
 if(r<0){int error=0;socklen_t n=sizeof(error);if(!waitFd(fd,true,deadline)||getsockopt(fd,SOL_SOCKET,SO_ERROR,&error,&n)||error){close(fd);return;}}
 const char* request="YIELD1\n";unsigned at=0;bool ok=true;
 while(at<7&&ok){if(!waitFd(fd,true,deadline)){ok=false;break;}ssize_t n=send(fd,request+at,7-at,
#ifdef MSG_NOSIGNAL
 MSG_NOSIGNAL
#else
 0
#endif
 );if(n>0)at+=n;else if(n==0||(errno!=EINTR&&errno!=EAGAIN&&errno!=EWOULDBLOCK))ok=false;}
 char reply[16];unsigned count=0;bool clean=false;
 while(ok&&count<sizeof(reply)){
  if(!waitFd(fd,false,deadline))break;
  ssize_t n=recv(fd,reply+count,sizeof(reply)-count,0);
  if(n>0){count+=n;if(count>=6){clean=count==6&&!memcmp(reply,"CLEAN\n",6);break;}}
  else if(n==0||(errno!=EINTR&&errno!=EAGAIN&&errno!=EWOULDBLOCK))break;
 }
 close(fd);
 // Factory priority: do not indefinitely block navigation on a failed HUD worker.
 // An uncertain handoff is NOT reported as successful cleanup.
 if(!clean){traceEvent("UNCERTAIN");fprintf(stderr,"supra-handoff: cleanup uncertain; factory priority after bounded wait\n");}
 else {traceEvent("CLEAN");if(getenv("SUPRA_HUD_TRACE"))fprintf(stderr,"supra-handoff: CLEAN at %lld\n",ms());}
}
static bool sharedFactoryPacket(const unsigned char* p,unsigned n){
 if(n<20)return false;
 unsigned service=(unsigned(p[0])<<8)|p[1],method=(unsigned(p[2])<<8)|p[3];
 if(service!=0xb006&&service!=0xb00e)return false;
 unsigned value=(unsigned(p[16])<<24)|(unsigned(p[17])<<16)|(unsigned(p[18])<<8)|p[19];
 if(method!=1)return value==(service==0xb006?200U:100U);
 const char* expected=service==0xb006?"BMW.IC.Guidance":"BMW.IC.List";unsigned chars=strlen(expected);
 if(value>512||n<20+value)return false;
 if(value==chars+1)return !memcmp(p+20,expected,chars)&&p[20+chars]==0;
 if(value==chars+4&&p[20]==239&&p[21]==187&&p[22]==191)return !memcmp(p+23,expected,chars)&&p[23+chars]==0;
 if(value!=chars*2+4||p[20]!=254||p[21]!=255)return false;
 for(unsigned i=0;i<chars;++i)if(p[22+2*i]||p[23+2*i]!=(unsigned char)expected[i])return false;
 return p[22+2*chars]==0&&p[23+2*chars]==0;
}
// Persistent mode forwards the exact pre-send packet to the admission supervisor.
// It replies only after the running worker has acknowledged removal.
static int brokerHandoff(const unsigned char* data,unsigned size){
 const char* path=getenv("SUPRA_HUD_BROKER_SOCKET");if(!path||!*path)return 0;
 const char* role=getenv("SUPRA_HUD_FACTORY_ROLE");if(!role||(strcmp(role,"nav")&&strcmp(role,"hmi")))return -1;
 sockaddr_un a;memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(strlen(path)>=sizeof(a.sun_path))return -1;strcpy(a.sun_path,path);
 int fd=socket(AF_UNIX,SOCK_STREAM,0);if(fd<0)return -1;
#ifndef MSG_NOSIGNAL
#ifdef SO_NOSIGPIPE
 int noPipe=1;if(setsockopt(fd,SOL_SOCKET,SO_NOSIGPIPE,&noPipe,sizeof(noPipe))){close(fd);return -1;}
#else
 close(fd);return -1;
#endif
#endif
 if(fcntl(fd,F_SETFL,O_NONBLOCK)<0){close(fd);return -1;}
 long long start=ms();if(start<0){close(fd);return -1;}long long deadline=start+3000;
 int rc=connect(fd,(sockaddr*)&a,sizeof(a));if(rc<0&&errno!=EINPROGRESS){close(fd);return 0;}
 if(rc<0){int e=0;socklen_t len=sizeof(e);if(!waitFd(fd,true,deadline)||getsockopt(fd,SOL_SOCKET,SO_ERROR,&e,&len)||e){close(fd);return 0;}}
 unsigned char header[12]={'P','R','E','1',0,0,0,0,0,0,0,0};header[4]=!strcmp(role,"hmi");for(unsigned i=0;i<4;++i)header[8+i]=(size>>(24-8*i))&255;
 for(unsigned part=0;part<2;++part){const unsigned char* bytes=part?data:header;unsigned count=part?size:12,at=0;
  while(at<count){if(!waitFd(fd,true,deadline)){close(fd);return -1;}ssize_t n=send(fd,bytes+at,count-at,
#ifdef MSG_NOSIGNAL
 MSG_NOSIGNAL
#else
 0
#endif
 );if(n>0)at+=n;else if(n==0||(errno!=EINTR&&errno!=EAGAIN)){close(fd);return -1;}}
 }
 char response[10];unsigned at=0;while(at<sizeof(response)&&waitFd(fd,false,deadline)){ssize_t n=recv(fd,response+at,sizeof(response)-at,0);if(n>0){at+=n;if(at>=6)break;}else if(n==0||(errno!=EINTR&&errno!=EAGAIN))break;}
 close(fd);bool clean=at==6&&!memcmp(response,"CLEAN\n",6);traceEvent(clean?"BROKER_CLEAN":"BROKER_UNCERTAIN");return clean?1:-1;
}
extern "C" int supraAdapter(void*,const void*,void*) __asm__("_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERK8TWeakPtrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE");
static int sendWithHandoff(const char* symbol,void* self,const void* socketRef,void* message){
 Sender original=(Sender)dlsym(RTLD_NEXT,symbol);
 if(!original){errno=ENOSYS;return -1;}
 const char* disable=getenv("SUPRA_HUD_DISABLE_FILE");if(disable&&*disable&&access(disable,F_OK)==0)return original(self,socketRef,message);
 const char* path=getenv("SUPRA_HUD_HANDOFF");if(!path||!*path)return original(self,socketRef,message);
 Length length=(Length)dlsym(RTLD_NEXT,"_ZN6SomeIP14CSomeIPMessage15getBytesWrittenEv");
 Data bytes=(Data)dlsym(RTLD_NEXT,"_ZN6SomeIP14CSomeIPMessage8getBytesEv");
 Address destination=(Address)dlsym(RTLD_NEXT,"_ZN6SomeIP14CSomeIPMessage21getDestinationAddressEv");
 if(!length||!bytes||!destination)return original(self,socketRef,message);
 sockaddr* dest=destination(message);unsigned n=length(message);unsigned char* data=bytes(message);
 if(getenv("SUPRA_HUD_BROKER_SOCKET")&&data&&n<=65552&&!sharedFactoryPacket(data,n))return original(self,socketRef,message);
 if(n>=16&&n<=65552&&data&&data[0]==0xb0&&(data[14]==0||data[14]==1)){
  // TCP messages may have no per-message destination; shared B0xx controller
  // requests then revoke conservatively. A supplied other destination is ignored.
  bool relevant=!dest;
  if(dest&&dest->sa_family==AF_INET){sockaddr_in* ip=(sockaddr_in*)dest;relevant=ntohl(ip->sin_addr.s_addr)==0xa030c760&&ntohs(ip->sin_port)==30502;}
  if(relevant){traceEvent("HANDOFF_CHECK");pthread_mutex_lock(&mutex);int broker=brokerHandoff(data,n);if(broker==0)handoff(path);pthread_mutex_unlock(&mutex);traceEvent("FACTORY_SEND");if(getenv("SUPRA_HUD_TRACE"))fprintf(stderr,"supra-handoff: factory send at %lld\n",ms());return original(self,socketRef,message);}
 }
 return original(self,socketRef,message);
}

extern "C" int supraAdapter(void* self,const void* socketRef,void* message){return sendWithHandoff(adapter,self,socketRef,message);}
// HmiMain3D imports the std::weak_ptr ABI; the reference stays opaque here.
static const char* hmiAdapter="_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERKSt8weak_ptrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE";
extern "C" int supraHmiAdapter(void*,const void*,void*) __asm__("_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERKSt8weak_ptrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE");
extern "C" int supraHmiAdapter(void* self,const void* socketRef,void* message){return sendWithHandoff(hmiAdapter,self,socketRef,message);}
