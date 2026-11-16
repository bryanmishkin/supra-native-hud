// Cooperative stop without PID signalling or a vehicle network connection.
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/select.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <signal.h>
#include <stdio.h>
#include <time.h>
static long long now(){timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return -1;return (long long)t.tv_sec*1000+t.tv_nsec/1000000;}
static bool ready(int fd,bool write,long long end){long long left=end-now();if(left<=0||left>5000)return false;timeval tv;tv.tv_sec=left/1000;tv.tv_usec=(left%1000)*1000;fd_set f;FD_ZERO(&f);FD_SET(fd,&f);return select(fd+1,write?0:&f,write?&f:0,0,&tv)>0;}
int main(int argc,char** argv){
 if(argc!=2)return 64;signal(SIGPIPE,SIG_IGN);sockaddr_un a;memset(&a,0,sizeof(a));a.sun_family=AF_UNIX;if(strlen(argv[1])>=sizeof(a.sun_path))return 64;strcpy(a.sun_path,argv[1]);int fd=socket(AF_UNIX,SOCK_STREAM,0);if(fd<0)return 2;long long start=now();if(start<0){close(fd);return 2;}long long end=start+5000;
 if(fcntl(fd,F_SETFL,O_NONBLOCK)<0){close(fd);return 2;}
 int r=connect(fd,(sockaddr*)&a,sizeof(a));if(r<0){if(errno!=EINPROGRESS||!ready(fd,true,end)){close(fd);return 2;}int e=0;socklen_t n=sizeof(e);if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&e,&n)||e){close(fd);return 2;}}
 const char* q="YIELD1\n";unsigned at=0;while(at<7){if(!ready(fd,true,end)){close(fd);return 2;}ssize_t n=send(fd,q+at,7-at,0);if(n<=0){close(fd);return 2;}at+=n;}
 char reply[6];at=0;while(at<6){if(!ready(fd,false,end)){close(fd);return 2;}ssize_t n=recv(fd,reply+at,6-at,0);if(n<=0){close(fd);return 2;}at+=n;}close(fd);
 if(memcmp(reply,"CLEAN\n",6))return 2;puts("CLEAN");return 0;
}
