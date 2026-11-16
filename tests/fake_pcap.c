/* Deterministic host fixture: no network or packet devices. */
#include <pcap.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
static char token; static double ticks; static int count;
static int mode(const char *s){const char *m=getenv("CAPTURE_FIXTURE");return m&&!strcmp(m,s);}
int clock_gettime(clockid_t id,struct timespec *t){(void)id;ticks+=mode("limit")?0.00001:1.0;t->tv_sec=(time_t)ticks;t->tv_nsec=(long)((ticks-t->tv_sec)*1e9);return 0;}
int usleep(useconds_t n){(void)n;return 0;}
pcap_t *pcap_open_live(const char *n,int snap,int promisc,int ms,char *err){(void)n;(void)ms;(void)err;if(snap!=65535||promisc)abort();return (pcap_t *)&token;}
int pcap_datalink(pcap_t *p){(void)p;return mode("badlink")?999:DLT_EN10MB;}
int pcap_compile(pcap_t *p,struct bpf_program *f,const char *s,int o,bpf_u_int32 m){(void)p;(void)f;(void)o;(void)m;if(!strstr(s,"160.48.199.96")||!strstr(s,"30502"))abort();return mode("badfilter")?-1:0;}
int pcap_setfilter(pcap_t *p,struct bpf_program *f){(void)p;(void)f;return 0;}
void pcap_freecode(struct bpf_program *f){(void)f;}
int pcap_setnonblock(pcap_t *p,int b,char *e){(void)p;(void)e;return b==1?0:-1;}
pcap_dumper_t *pcap_dump_fopen(pcap_t *p,FILE *f){char h[24]={0};(void)p;fwrite(h,1,24,f);return (pcap_dumper_t *)f;}
int pcap_next_ex(pcap_t *p,struct pcap_pkthdr **h,const u_char **data){static struct pcap_pkthdr header;static unsigned char buf[65535];(void)p;if(mode("empty"))return 0;if(mode("readerror"))return -1;if(!mode("limit")&&count++>1)return 0;header.caplen=header.len=mode("limit")?65535:64;*h=&header;*data=buf;return 1;}
void pcap_dump(u_char *o,const struct pcap_pkthdr *h,const u_char *d){char v[16]={0};fwrite(v,1,16,(FILE *)o);fwrite(d,1,h->caplen,(FILE *)o);}
int pcap_dump_flush(pcap_dumper_t *o){return mode("writeerror")?-1:fflush((FILE *)o);}
void pcap_dump_close(pcap_dumper_t *o){fclose((FILE *)o);}
int pcap_stats(pcap_t *p,struct pcap_stat *s){(void)p;memset(s,0,sizeof(*s));s->ps_drop=mode("drops")?1:0;return 0;}
void pcap_close(pcap_t *p){(void)p;}
char *pcap_geterr(pcap_t *p){(void)p;return "fixture";}
int pcap_findalldevs(pcap_if_t **p,char *e){(void)e;*p=0;return 0;}
void pcap_freealldevs(pcap_if_t *p){(void)p;}
