/* Exact-image configuration transaction; preserves original inode via hard link.
   No remount, process signal, reboot, watchdog control or shell utilities. */
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#ifndef SUPRA_STARTUP_TARGET
#define SUPRA_STARTUP_TARGET "/opt/nav/eceusa/bin/NavigationEceUsa.cfg"
#endif
#define BACKUP SUPRA_STARTUP_TARGET ".supra-original"
#define TEMP SUPRA_STARTUP_TARGET ".supra-pending"
#define LOCK SUPRA_STARTUP_TARGET ".supra-lock"
#define LIMIT (512*1024)
static unsigned char before[LIMIT],after[LIMIT],check[LIMIT];
static ssize_t read_file(const char *p,unsigned char *buf) {
 struct stat s;int fd;size_t at=0;ssize_t n;
 if(lstat(p,&s)||!S_ISREG(s.st_mode)||s.st_size<=0||s.st_size>LIMIT)return -1;
 fd=open(p,O_RDONLY);if(fd<0)return -1;
 while(at<(size_t)s.st_size){n=read(fd,buf+at,(size_t)s.st_size-at);if(n<0&&errno==EINTR)continue;if(n<=0){close(fd);return -1;}at+=(size_t)n;}
 close(fd);return (ssize_t)at;
}
static int equal(const char *p,const unsigned char *buf,size_t n) {ssize_t got=read_file(p,check);return got==(ssize_t)n&&!memcmp(check,buf,n);}
int main(int argc,char **argv) {
 ssize_t bn,an;struct stat original,saved;int fd=-1,rc=2,locked=0,temporary=0;size_t at;ssize_t n;
 if(argc!=4|| (strcmp(argv[1],"apply")&&strcmp(argv[1],"rollback")))return 64;
 bn=read_file(argv[2],before);an=read_file(argv[3],after);
 if(bn<=0||an<=0||(bn==an&&!memcmp(before,after,(size_t)bn)))return 2;
 if(mkdir(LOCK,0700)){perror("transaction lock");return 2;}locked=1;
 if(!strcmp(argv[1],"apply")) {
  if(!equal(SUPRA_STARTUP_TARGET,before,(size_t)bn)||lstat(SUPRA_STARTUP_TARGET,&original)||!S_ISREG(original.st_mode))goto done;
  if(link(SUPRA_STARTUP_TARGET,BACKUP)){perror("original backup");goto done;}
  sync(); /* Preserve the original inode before replacing the visible entry. */
  fd=open(TEMP,O_CREAT|O_EXCL|O_WRONLY,0600);if(fd<0)goto done;temporary=1;
  for(at=0;at<(size_t)an;at+=(size_t)n){n=write(fd,after+at,(size_t)an-at);if(n<0&&errno==EINTR){n=0;continue;}if(n<=0)goto done;}
  if(fchown(fd,original.st_uid,original.st_gid)||fchmod(fd,original.st_mode&07777)||fsync(fd))goto done;
  if(close(fd)){fd=-1;goto done;}fd=-1;
  if(!equal(SUPRA_STARTUP_TARGET,before,(size_t)bn)||!equal(TEMP,after,(size_t)an))goto done;
  if(rename(TEMP,SUPRA_STARTUP_TARGET))goto done;temporary=0;sync();
  if(!equal(SUPRA_STARTUP_TARGET,after,(size_t)an))goto done;
 } else {
  if(!equal(SUPRA_STARTUP_TARGET,after,(size_t)an)||!equal(BACKUP,before,(size_t)bn)||lstat(BACKUP,&saved)||!S_ISREG(saved.st_mode))goto done;
  if(rename(BACKUP,SUPRA_STARTUP_TARGET))goto done;sync();
  if(lstat(SUPRA_STARTUP_TARGET,&original)||original.st_ino!=saved.st_ino||original.st_dev!=saved.st_dev||!equal(SUPRA_STARTUP_TARGET,before,(size_t)bn))goto done;
 }
 rc=0;puts(!strcmp(argv[1],"apply")?"APPLY_VERIFIED":"ROLLBACK_VERIFIED");
 done:
 if(fd>=0)close(fd);if(temporary)unlink(TEMP);if(locked)rmdir(LOCK);
 if(rc)fprintf(stderr,"Transaction refused or incomplete; preserve backup and inspect before proceeding\n");
 return rc;
}
