/* Passive, non-promiscuous, bounded capture. No packet injection or vehicle requests. */
#include <pcap.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <ctype.h>
#define BYTE_LIMIT (8UL*1024UL*1024UL)
#define PACKET_LIMIT 4096UL
static void deadline(int sig) { (void)sig; _exit(124); }
static double now(void) { struct timespec t; if(clock_gettime(CLOCK_MONOTONIC,&t)) return -1; return t.tv_sec+t.tv_nsec/1e9; }
int main(int argc,char **argv) {
 char err[PCAP_ERRBUF_SIZE]; pcap_t *p; pcap_dumper_t *out; struct bpf_program filter;
 struct pcap_stat stats; unsigned long packets=0,bytes=24; double start,t; int rc=0;
 const char *reason="duration";
 const char *expr="(host 160.48.199.96 or host 160.48.199.97) and (tcp or udp) and (port 30501 or port 30502 or port 30503)";
 signal(SIGALRM,deadline); alarm(20);
 if(argc==2 && !strcmp(argv[1],"--list")) {
  pcap_if_t *head,*i;
  if(pcap_findalldevs(&head,err)<0) {fprintf(stderr,"%s\n",err);return 2;}
  for(i=head;i;i=i->next) printf("%s\n",i->name);
  pcap_freealldevs(head); return 0;
 }
 if(argc!=3 || strcmp(argv[1],"--capture") || !argv[2][0] || strlen(argv[2])>32) {
  fprintf(stderr,"Usage: %s --list | --capture INTERFACE\n",argv[0]);return 2;
 }
 {const char *c;for(c=argv[2];*c;++c)if(!isalnum((unsigned char)*c)&&*c!='_'&&*c!='-'){return 2;}}
 p=pcap_open_live(argv[2],65535,0,100,err);
 if(!p){fprintf(stderr,"open: %s\n",err);return 2;}
 if(pcap_datalink(p)!=DLT_EN10MB){fprintf(stderr,"Unsupported link type\n");pcap_close(p);return 2;}
 if(pcap_compile(p,&filter,expr,1,0xffffffff)<0){fprintf(stderr,"filter: %s\n",pcap_geterr(p));pcap_close(p);return 2;}
 rc=pcap_setfilter(p,&filter);pcap_freecode(&filter);
 if(rc<0 || pcap_setnonblock(p,1,err)<0){fprintf(stderr,"Filter/nonblocking setup failed\n");pcap_close(p);return 2;}
 out=pcap_dump_fopen(p,stdout);
 if(!out){fprintf(stderr,"output: %s\n",pcap_geterr(p));pcap_close(p);return 2;}
 start=now();rc=0;
 if(start<0){reason="clock_error";rc=2;}
 while(rc==0){
  struct pcap_pkthdr *h; const u_char *data; int n;
  t=now();if(t<start){reason="clock_error";rc=2;break;}if(t-start>=15.0)break;
  n=pcap_next_ex(p,&h,&data);
  if(n==0){usleep(10000);continue;}
  if(n<0){reason="read_error";rc=2;break;}
  if(h->caplen>65535 || h->caplen>h->len){reason="invalid_packet";rc=2;break;}
  if(bytes+16+h->caplen>BYTE_LIMIT || packets>=PACKET_LIMIT){reason="limit";rc=3;break;}
  pcap_dump((u_char *)out,h,data);bytes+=16+h->caplen;++packets;
  if(pcap_dump_flush(out)!=0){reason="write_error";rc=2;break;}
 }
 memset(&stats,0,sizeof(stats));
 if(pcap_stats(p,&stats)<0){reason="stats_unavailable";rc=2;}
 else if(stats.ps_drop || stats.ps_ifdrop){reason="packet_drops";rc=3;}
 if(pcap_dump_flush(out)!=0){reason="write_error";rc=2;}
 fprintf(stderr,"{\"schema\":1,\"packets\":%lu,\"pcap_bytes\":%lu,\"elapsed_s\":%.3f,\"drops\":%u,\"interface_drops\":%u,\"reason\":\"%s\",\"promiscuous\":false,\"transmitted\":0}\n",packets,bytes,now()-start,stats.ps_drop,stats.ps_ifdrop,reason);
 pcap_dump_close(out);pcap_close(p);alarm(0);return rc;
}
