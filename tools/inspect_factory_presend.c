/* Bounded no-drawing broker: records factory PRE messages, then releases sender. */
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <sys/select.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#include <errno.h>
static volatile sig_atomic_t done;
static void stop(int sig){(void)sig;done=1;}
static int readn(int fd,unsigned char* b,unsigned n){unsigned at=0;while(at<n){ssize_t r=recv(fd,b+at,n-at,0);if(r<=0)return 0;at+=(unsigned)r;}return 1;}
int main(int argc,char** argv){int server,fd;struct sockaddr_un a;FILE* out;time_t end;unsigned count=0,total=0;unsigned char h[12],b[65552];if(argc!=3)return 64;umask(077);signal(SIGPIPE,SIG_IGN);signal(SIGTERM,stop);signal(SIGINT,stop);memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(strlen(argv[1])>=sizeof(a.sun_path))return 2;strcpy(a.sun_path,argv[1]);server=socket(AF_UNIX,SOCK_STREAM,0);if(server<0||bind(server,(struct sockaddr*)&a,sizeof(a))||listen(server,16))return 2;out=fopen(argv[2],"wb");if(!out){close(server);unlink(argv[1]);return 2;}end=time(0)+90;puts("INSPECT_READY_NO_DRAWING");fflush(stdout);
while(!done&&time(0)<end&&count<4096&&total<4194304){fd_set set;struct timeval t;int rc;FD_ZERO(&set);FD_SET(server,&set);t.tv_sec=1;t.tv_usec=0;rc=select(server+1,&set,0,0,&t);if(rc<=0)continue;fd=accept(server,0,0);if(fd<0)continue;t.tv_sec=1;t.tv_usec=0;setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&t,sizeof(t));if(readn(fd,h,12)&&!memcmp(h,"PRE1",4)){unsigned n=((unsigned)h[8]<<24)|((unsigned)h[9]<<16)|((unsigned)h[10]<<8)|h[11];if(n>=16&&n<=sizeof(b)&&readn(fd,b,n)){fwrite(h,1,12,out);fwrite(b,1,n,out);fflush(out);count++;total+=n+12;send(fd,"CLEAN\n",6,0);}}close(fd);}
fclose(out);close(server);unlink(argv[1]);printf("INSPECT_COMPLETE packets=%u bytes=%u\n",count,total);return 0;}
