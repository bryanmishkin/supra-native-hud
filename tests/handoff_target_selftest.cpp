// Isolated fake-factory ABI test. No network/vehicle endpoint, no controller attach.
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
struct Message {unsigned size;unsigned char data[32];sockaddr_in destination;bool nullDestination;};
extern "C" int sendMessage(void*,const void*,void*) __asm__("_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERK8TWeakPtrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE");
int main(int argc,char** argv){
 if(argc!=2)return 64;
 sockaddr_un address;memset(&address,0,sizeof(address));address.sun_family=AF_UNIX;
 if(strlen(argv[1])>=sizeof(address.sun_path))return 64;
 strcpy(address.sun_path,argv[1]);
 int server=socket(AF_UNIX,SOCK_STREAM,0);if(server<0)return 2;
 if(bind(server,(sockaddr*)&address,sizeof(address))||listen(server,1)){close(server);return 2;}
 pid_t child=fork();if(child<0){close(server);unlink(argv[1]);return 2;}
 if(child==0){alarm(5);int peer=accept(server,0,0);if(peer<0)_exit(2);char b[7];unsigned at=0;while(at<7){ssize_t n=read(peer,b+at,7-at);if(n<=0)_exit(2);at+=n;}if(memcmp(b,"YIELD1\n",7))_exit(2);if(write(peer,"CLEAN\n",6)!=6)_exit(2);close(peer);close(server);_exit(0);}
 close(server);setenv("SUPRA_HUD_HANDOFF",argv[1],1);Message m;memset(&m,0,sizeof(m));m.size=32;m.data[0]=0xb0;m.data[1]=6;m.nullDestination=true;
 int result=sendMessage(0,0,&m),status=0;waitpid(child,&status,0);unlink(argv[1]);
 if(result!=37||!WIFEXITED(status)||WEXITSTATUS(status)!=0)return 2;
 puts("PASS: isolated pre-send hook ABI and CLEAN handshake; no factory process contacted");return 0;
}
