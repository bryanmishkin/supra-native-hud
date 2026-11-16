#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
struct Message {unsigned size;unsigned char data[32];sockaddr_in destination;bool nullDestination;};
extern "C" unsigned length(void*) __asm__("_ZN6SomeIP14CSomeIPMessage15getBytesWrittenEv");
extern "C" unsigned length(void* m){return ((Message*)m)->size;}
extern "C" unsigned char* bytes(void*) __asm__("_ZN6SomeIP14CSomeIPMessage8getBytesEv");
extern "C" unsigned char* bytes(void* m){return ((Message*)m)->data;}
extern "C" sockaddr* address(void*) __asm__("_ZN6SomeIP14CSomeIPMessage21getDestinationAddressEv");
extern "C" sockaddr* address(void* m){return ((Message*)m)->nullDestination?0:(sockaddr*)&((Message*)m)->destination;}
extern "C" int sendMessage(void*,const void*,void*) __asm__("_ZN6SomeIP22CSomeIPProtocolAdapter13doSendMessageERK8TWeakPtrI21CSocketSenderReceiverI11CDispatcherS0_EERNS_14CSomeIPMessageE");
extern "C" int sendMessage(void*,const void*,void*){puts("FACTORY_SEND");fflush(stdout);return 37;}
