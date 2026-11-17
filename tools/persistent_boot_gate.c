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
/* One bounded last-decision record per gate; never log inherited environment. */
static void record(const char* event){
 char path[512],body[256];int fd,n;
 if(!private_path(SUPRA_RELEASE,1))return;
 snprintf(path,sizeof(path),"%s/last-gate-%s.status",SUPRA_RELEASE,SUPRA_ROLE);
 fd=open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);if(fd<0)return;
 n=snprintf(body,sizeof(body),"role=%s\npid=%ld\nevent=%s\n",SUPRA_ROLE,(long)getpid(),event);
 if(n>0&&n<(int)sizeof(body)){ssize_t ignored=write(fd,body,(size_t)n);(void)ignored;fsync(fd);}close(fd);
}
static int token(const char* p,const char* text){char b[64];int fd;ssize_t n;if(!private_path(p,0))return 0;fd=open(p,O_RDONLY);if(fd<0)return 0;n=read(fd,b,sizeof(b));close(fd);return n==(ssize_t)strlen(text)&&!memcmp(b,text,(size_t)n);}
static const char* factory_preload="libEGL_X.gpp.so:libGLESv2_X_FORWARD.gpp.so:libKD_X.gpp.so";
static int active(void){
 const char* inherited=getenv("LD_PRELOAD");int fd;unsigned i;
 if(inherited&&*inherited&&(strcmp(SUPRA_ROLE,"hmi")||strcmp(inherited,factory_preload))){record("inherited-preload-rejected");return 0;}
 if(!private_path(SUPRA_RELEASE,1))return 0;
 if(!access(SUPRA_RELEASE "/disabled",F_OK)){record("persistent-disable-present");return 0;}
 if(!private_path(SUPRA_RELEASE "/libsupra-navigation-handoff-experimental.so",0)||!private_path(SUPRA_RELEASE "/supra-resident-qnx",0)||!private_path(SUPRA_RELEASE "/supra-standalone-parked-qnx",0)||!private_path(SUPRA_RELEASE "/supra-profile.bin",0)){record("missing-or-insecure-artifact");return 0;}
 if(mkdir(SUPRA_RUNTIME,0700)&&errno!=EEXIST)return 0;if(!private_path(SUPRA_RUNTIME,1))return 0;
 if(token(SUPRA_RELEASE "/enabled","SUPRA-PERSISTENT-1\n"))return 1;
 if(token(SUPRA_RUNTIME "/trial-boot","SUPRA-TRIAL-1\n"))return 1;
 if(!token(SUPRA_RELEASE "/armed","SUPRA-TRIAL-1\n")){
  if(access(SUPRA_RUNTIME "/activating",F_OK)){record("not-armed-or-enabled");return 0;}
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
   int error=open(SUPRA_RUNTIME "/resident.stderr",O_WRONLY|O_CREAT|O_TRUNC,0600);if(error>=0){dup2(error,2);if(error>2)close(error);}
   unsetenv("LD_PRELOAD");
   execl(SUPRA_RELEASE "/supra-resident-qnx","supra-resident-qnx",SUPRA_RELEASE,SUPRA_RUNTIME,"vlan73",(char*)0);_exit(127);
  }
  waitpid(first,0,0);
 }else if(errno!=EEXIST)return 0;
 for(i=0;i<200;++i){if(ready())return 1;usleep(10000);}record("resident-readiness-timeout");return 0;
}
int main(int argc,char** argv){char preload[512],original[256];const char* inherited=getenv("LD_PRELOAD");(void)argc;
 record("gate-entered");
 original[0]=0;if(inherited&&strlen(inherited)<sizeof(original))strcpy(original,inherited);
 snprintf(preload,sizeof(preload),"%s%s%s",SUPRA_RELEASE "/libsupra-navigation-handoff-experimental.so",original[0]?":":"",original);
 if(active()&&supervisor()){
  record("hook-environment-selected");
  if(setenv("SUPRA_HUD_FACTORY_ROLE",SUPRA_ROLE,1)||setenv("SUPRA_HUD_BROKER_SOCKET",SUPRA_RUNTIME "/factory.sock",1)||setenv("SUPRA_HUD_HANDOFF",SUPRA_RUNTIME "/active.jsonl.handoff",1)||setenv("SUPRA_HUD_DISABLE_FILE",SUPRA_RELEASE "/disabled",1)||setenv("SUPRA_HUD_TRACE_FILE",SUPRA_RUNTIME "/hook.log",1)||setenv("LD_PRELOAD",preload,1)){record("hook-environment-failed");if(original[0])setenv("LD_PRELOAD",original,1);else unsetenv("LD_PRELOAD");}
 }
 argv[0]=(char*)SUPRA_FACTORY;execv(SUPRA_FACTORY,argv);perror("original factory exec");return 127;
}
