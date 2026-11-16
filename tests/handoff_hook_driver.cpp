#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
struct Message {unsigned size;unsigned char data[32];sockaddr_in destination;bool nullDestination;};
extern "C" int sendMessage(void*,const void*,void*) __asm__("_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERK8TWeakPtrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE");
int main(int argc,char** argv){Message m;memset(&m,0,sizeof(m));m.size=32;m.data[0]=0xb0;m.data[1]=6;m.destination.sin_family=AF_INET;m.destination.sin_port=htons(30502);m.destination.sin_addr.s_addr=htonl(0xa030c760);
 if(argc==2){if(!strcmp(argv[1],"null-destination"))m.nullDestination=true;if(!strcmp(argv[1],"non-hud"))m.data[0]=0xa0;if(!strcmp(argv[1],"keepalive"))m.data[0]=m.data[1]=255;if(!strcmp(argv[1],"other-destination"))m.destination.sin_addr.s_addr=htonl(0x7f000001);}
 return sendMessage(0,0,&m)==37?0:2;}
