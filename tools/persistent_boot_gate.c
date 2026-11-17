/* Factory-supervised same-PID exec; one-boot acceptance or committed persistence. */
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#ifndef SUPRA_RELEASE
#define SUPRA_RELEASE "/var/opt/supra-hud/v1"
#endif
#ifndef SUPRA_RUNTIME
#define SUPRA_RUNTIME "/tmp/supra-hud-v1"
#endif
#ifndef SUPRA_FACTORY
#define SUPRA_FACTORY "/opt/nav/eceusa/bin/NavNBTEvoController"
#endif
#ifndef SUPRA_ROLE
#define SUPRA_ROLE "nav"
#endif
static int private_path(const char* p,int dir){struct stat s;return !lstat(p,&s)&&s.st_uid==geteuid()&&!(s.st_mode&0022)&&(dir?S_ISDIR(s.st_mode):S_ISREG(s.st_mode));}
static int token(const char* p,const char* text){char b[64];int fd;ssize_t n;if(!private_path(p,0))return 0;fd=open(p,O_RDONLY);if(fd<0)return 0;n=read(fd,b,sizeof(b));close(fd);return n==(ssize_t)strlen(text)&&!memcmp(b,text,(size_t)n);}
static int active(void){
 const char* inherited=getenv("LD_PRELOAD");int fd;unsigned i;
 if((inherited&&*inherited)||!private_path(SUPRA_RELEASE,1)||!access(SUPRA_RELEASE "/disabled",F_OK))return 0;
 if(!private_path(SUPRA_RELEASE "/libsupra-navigation-handoff-experimental.so",0)||!private_path(SUPRA_RELEASE "/supra-resident-qnx",0)||!private_path(SUPRA_RELEASE "/supra-standalone-parked-qnx",0)||!private_path(SUPRA_RELEASE "/supra-profile.bin",0))return 0;
 if(mkdir(SUPRA_RUNTIME,0700)&&errno!=EEXIST)return 0;if(!private_path(SUPRA_RUNTIME,1))return 0;
 if(token(SUPRA_RELEASE "/enabled","SUPRA-PERSISTENT-1\n"))return 1;
 if(token(SUPRA_RUNTIME "/trial-boot","SUPRA-TRIAL-1\n"))return 1;
 if(!token(SUPRA_RELEASE "/armed","SUPRA-TRIAL-1\n")){
  if(access(SUPRA_RUNTIME "/activating",F_OK))return 0;
  for(i=0;i<200;++i){if(token(SUPRA_RUNTIME "/trial-boot","SUPRA-TRIAL-1\n"))return 1;usleep(10000);}return 0;
 }
 if(mkdir(SUPRA_RUNTIME "/activating",0700)){
  if(errno!=EEXIST)return 0;
  for(i=0;i<200;++i){if(token(SUPRA_RUNTIME "/trial-boot","SUPRA-TRIAL-1\n"))return 1;usleep(10000);}return 0;
 }
 /* One winner consumes a persistent token; both gates share this RAM boot. */
 if(link(SUPRA_RELEASE "/armed",SUPRA_RELEASE "/consumed"))return 0;
 if(unlink(SUPRA_RELEASE "/armed"))return 0;sync();
 fd=open(SUPRA_RUNTIME "/trial-boot",O_WRONLY|O_CREAT|O_EXCL,0600);if(fd<0)return 0;
 if(write(fd,"SUPRA-TRIAL-1\n",14)!=14){close(fd);return 0;}close(fd);return 1;
}
static int ready(void){struct stat s;return token(SUPRA_RUNTIME "/ready","CAPTURE_READY\n")&&!lstat(SUPRA_RUNTIME "/factory.sock",&s)&&S_ISSOCK(s.st_mode);}
static int supervisor(void){
 unsigned i;pid_t first;
 if(!mkdir(SUPRA_RUNTIME "/launch",0700)){
  first=fork();if(first<0)return 0;
  if(!first){pid_t p;setsid();p=fork();if(p<0)_exit(127);if(p>0)_exit(0);
   int fd=open("/dev/null",O_RDWR);if(fd>=0){dup2(fd,0);dup2(fd,1);dup2(fd,2);if(fd>2)close(fd);}
   execl(SUPRA_RELEASE "/supra-resident-qnx","supra-resident-qnx",SUPRA_RELEASE,SUPRA_RUNTIME,"vlan73",(char*)0);_exit(127);
  }
  waitpid(first,0,0);
 }else if(errno!=EEXIST)return 0;
 for(i=0;i<200;++i){if(ready())return 1;usleep(10000);}return 0;
}
int main(int argc,char** argv){(void)argc;
 if(active()&&supervisor()){
  if(setenv("SUPRA_HUD_FACTORY_ROLE",SUPRA_ROLE,1)||setenv("SUPRA_HUD_BROKER_SOCKET",SUPRA_RUNTIME "/factory.sock",1)||setenv("SUPRA_HUD_HANDOFF",SUPRA_RUNTIME "/active.jsonl.handoff",1)||setenv("SUPRA_HUD_DISABLE_FILE",SUPRA_RELEASE "/disabled",1)||setenv("SUPRA_HUD_TRACE_FILE",SUPRA_RUNTIME "/hook.log",1)||setenv("LD_PRELOAD",SUPRA_RELEASE "/libsupra-navigation-handoff-experimental.so",1))unsetenv("LD_PRELOAD");
 }
 argv[0]=(char*)SUPRA_FACTORY;execv(SUPRA_FACTORY,argv);perror("original factory exec");return 127;
}
