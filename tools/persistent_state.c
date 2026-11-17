#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#define ROOT "/var/opt/supra-hud/v1"
int main(int argc,char** argv){const char* path;const char* body;int fd;struct stat st;if(argc!=2)return 64;
 if(lstat(ROOT,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&0022))return 2;
 if(!strcmp(argv[1],"arm")){path=ROOT "/armed";body="SUPRA-TRIAL-1\n";if(!access(ROOT "/consumed",F_OK)||!access(ROOT "/enabled",F_OK)||!access(ROOT "/disabled",F_OK))return 2;}
 else if(!strcmp(argv[1],"commit")){path=ROOT "/enabled";body="SUPRA-PERSISTENT-1\n";if(access(ROOT "/consumed",F_OK)||!access(ROOT "/disabled",F_OK))return 2;}
 else if(!strcmp(argv[1],"disable")){path=ROOT "/disabled";body="Disabled by operator\n";}
 else return 64;
 fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0600);if(fd<0)return 2;if(write(fd,body,strlen(body))!=(ssize_t)strlen(body)||fsync(fd)){close(fd);return 2;}if(close(fd))return 2;sync();puts("STATE_SAVED");return 0;
}
