#ifndef SUPRA_WORKER_OUTCOME_HPP
#define SUPRA_WORKER_OUTCOME_HPP
#include <string>
#include <cstdio>
namespace supra {
struct WorkerOutcome {
 bool valid,clean,foreign,unknown;unsigned frames;std::string reason;
 WorkerOutcome():valid(false),clean(false),foreign(false),unknown(false),frames(0){}
};
// Accept only the worker's complete terminal record and the known DSI preamble.
inline WorkerOutcome workerOutcome(std::string text){
 WorkerOutcome o;
 while(text.compare(0,12,"[DsiClient] ")==0){size_t e=text.find('\n');if(e==std::string::npos)return o;text.erase(0,e+1);}
 char reason[256]={0},clean[6]={0},foreign[6]={0},unknown[6]={0};int end=0;
 int n=std::sscanf(text.c_str(),"{\"reason\":\"%255[^\"]\",\"frames\":%u,\"cleanup_verified\":%5[a-z],\"factory_activity\":%5[a-z],\"monitor_unknown\":%5[a-z],\"automatic_resume\":false,\"shared_instance_preserved\":true}%n",reason,&o.frames,clean,foreign,unknown,&end);
 if(n!=5||!end||text.substr(end)!="\n")return o;
 std::string a(clean),b(foreign),c(unknown);if((a!="true"&&a!="false")||(b!="true"&&b!="false")||(c!="true"&&c!="false"))return o;
 o.reason=reason;if(o.reason.find_first_of("\r\n\\")!=std::string::npos)return WorkerOutcome();
 o.valid=true;o.clean=a=="true";o.foreign=b=="true";o.unknown=c=="true";return o;
}
inline bool inputRecovery(const WorkerOutcome& o){return o.valid&&o.clean&&!o.foreign&&!o.unknown&&(o.reason.compare(0,14,"rpm_transport:")==0||o.reason=="RPM stale"||o.reason=="invalid/stale RPM");}
inline bool poolRecovery(const WorkerOutcome& o){return o.valid&&o.clean&&!o.foreign&&!o.unknown&&o.frames==0&&o.reason=="bitmap pool in use";}
inline const char* unexpectedExit(const WorkerOutcome& o,bool exited){
 if(!exited)return "worker terminated by signal";
 if(!o.valid)return "worker result missing or malformed";
 if(!o.clean)return "worker cleanup unverified";
 if(o.unknown)return "worker monitor uncertainty after clean exit";
 if(o.foreign)return "worker factory activity after clean exit";
 return "worker unexpected clean exit";
}
}
#endif
