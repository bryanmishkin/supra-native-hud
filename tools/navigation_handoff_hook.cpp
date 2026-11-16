// Experimental pre-send interposer. NEVER install/preload without target validation.
// Filters exact cluster endpoint and defers factory sending for a bounded handoff.
#include <dlfcn.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <sys/un.h>
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
 if(!clean)fprintf(stderr,"supra-handoff: cleanup uncertain; factory priority after bounded wait\n");
}
extern "C" int supraAdapter(void*,const void*,void*) __asm__("_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERK8TWeakPtrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE");
extern "C" int supraAdapter(void* self,const void* socketRef,void* message){
 Sender original=(Sender)dlsym(RTLD_NEXT,adapter);
 if(!original){errno=ENOSYS;return -1;}
 const char* path=getenv("SUPRA_HUD_HANDOFF");if(!path||!*path)return original(self,socketRef,message);
 Length length=(Length)dlsym(RTLD_NEXT,"_ZN6SomeIP14CSomeIPMessage15getBytesWrittenEv");
 Data bytes=(Data)dlsym(RTLD_NEXT,"_ZN6SomeIP14CSomeIPMessage8getBytesEv");
 Address destination=(Address)dlsym(RTLD_NEXT,"_ZN6SomeIP14CSomeIPMessage21getDestinationAddressEv");
 if(!length||!bytes||!destination)return original(self,socketRef,message);
 sockaddr* dest=destination(message);unsigned n=length(message);unsigned char* data=bytes(message);
 if(n>=16&&n<=65552&&data&&data[0]==0xb0&&(data[14]==0||data[14]==1)){
  // TCP messages may have no per-message destination; shared B0xx controller
  // requests then revoke conservatively. A supplied other destination is ignored.
  bool relevant=!dest;
  if(dest&&dest->sa_family==AF_INET){sockaddr_in* ip=(sockaddr_in*)dest;relevant=ntohl(ip->sin_addr.s_addr)==0xa030c760&&ntohs(ip->sin_port)==30502;}
  if(relevant){pthread_mutex_lock(&mutex);handoff(path);pthread_mutex_unlock(&mutex);return original(self,socketRef,message);}
 }
 return original(self,socketRef,message);
}
