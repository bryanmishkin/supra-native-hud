/* Target-only fixture: no vehicle I/O, logs selected inherited state. */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc,char **argv) {
 int i;const char *p=getenv("LD_PRELOAD");char cwd[256];
 printf("PID=%ld\nPRELOAD=%s\n",(long)getpid(),p?p:"none");
 if(getcwd(cwd,sizeof(cwd)))printf("CWD=%s\n",cwd);
 for(i=1;i<argc;++i)printf("ARG=%s\n",argv[i]);
 puts("FAKE_FACTORY_ONLY");return 0;
}
