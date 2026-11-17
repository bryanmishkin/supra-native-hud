/* One-use factory-started hook gate. Never starts a HUD worker or stops a PID. */
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#ifndef SUPRA_BOOT_ROOT
#define SUPRA_BOOT_ROOT "/var/opt/supra-hud/boot-trial"
#endif
#ifndef SUPRA_FACTORY_PATH
#define SUPRA_FACTORY_PATH "/opt/nav/eceusa/bin/NavNBTEvoController"
#endif
#ifndef SUPRA_STATE_ROOT
#define SUPRA_STATE_ROOT "/tmp/supra-hud-boottrial"
#endif
#define ARM_TEXT "SUPRA-BOOT-TRIAL-1\n"
static int regular_private(const char *path) {
 struct stat s;
 return !lstat(path,&s) && S_ISREG(s.st_mode) && s.st_uid==geteuid() && !(s.st_mode&0022);
}
static int activate(void) {
 const char *preload=getenv("LD_PRELOAD");
 struct stat root; char token[64]; ssize_t n; int fd;
 if(lstat(SUPRA_BOOT_ROOT,&root)||!S_ISDIR(root.st_mode)||root.st_uid!=geteuid()||(root.st_mode&0022))return 0;
 if(!access(SUPRA_BOOT_ROOT "/disabled",F_OK)||(preload&&*preload))return 0;
 if(!regular_private(SUPRA_BOOT_ROOT "/armed")||!regular_private(SUPRA_BOOT_ROOT "/libsupra-navigation-handoff-experimental.so"))return 0;
 fd=open(SUPRA_BOOT_ROOT "/armed",O_RDONLY);if(fd<0)return 0;
 n=read(fd,token,sizeof(token));close(fd);
 if(n!=(ssize_t)strlen(ARM_TEXT)||memcmp(token,ARM_TEXT,(size_t)n))return 0;
 /* Exclusive hard-link consumes the ticket before loading experimental code.
    If a previous ticket exists, fail closed. Never rearm automatically. */
 if(link(SUPRA_BOOT_ROOT "/armed",SUPRA_BOOT_ROOT "/consumed"))return 0;
 if(unlink(SUPRA_BOOT_ROOT "/armed"))return 0;
 sync();
 return 1;
}
int main(int argc,char **argv) {
 (void)argc;
 if(activate()) {
  if(setenv("SUPRA_HUD_HANDOFF",SUPRA_STATE_ROOT "/active.jsonl.handoff",1)||
     setenv("SUPRA_HUD_DISABLE_FILE",SUPRA_BOOT_ROOT "/disabled",1)||
     setenv("SUPRA_HUD_TRACE_FILE",SUPRA_BOOT_ROOT "/handoff.log",1)||
     setenv("LD_PRELOAD",SUPRA_BOOT_ROOT "/libsupra-navigation-handoff-experimental.so",1)) {
   /* No inherited preload was present on this path. */
   unsetenv("LD_PRELOAD");unsetenv("SUPRA_HUD_HANDOFF");unsetenv("SUPRA_HUD_TRACE_FILE");
  }
 }
 argv[0]=(char *)SUPRA_FACTORY_PATH;
 execv(SUPRA_FACTORY_PATH,argv);
 perror("supra boot gate: original factory exec failed");return 127;
}
