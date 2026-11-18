#define SUPRA_RESIDENT_NO_MAIN
#include "../tools/supra_resident.cpp"
#include <cassert>
static std::string terminal(const char* reason){return std::string("{\"reason\":\"")+reason+"\",\"frames\":9,\"cleanup_verified\":true,\"factory_activity\":false,\"monitor_unknown\":false,\"automatic_resume\":false,\"shared_instance_preserved\":true}\n";}
int main(){
 char tmp[]="/tmp/supra-retention-XXXXXX";assert(mkdtemp(tmp));std::string root=std::string(tmp)+"/root",state=std::string(tmp)+"/ram";assert(!mkdir(root.c_str(),0700)&&!mkdir(state.c_str(),0700));
 assert(privateDir(root));Resident r(root.c_str(),state.c_str());r.cleanupProven=true;r.lastWaitStatus=512;
 saveText(state+"/worker.result",terminal("RPM stale"));saveText(state+"/active.jsonl","{\"rpm\":6500}\n");r.evidence("worker_exit",false);
 std::string first=recordTail(root+"/fault-first.json",1000000);assert(first.find("6500")!=std::string::npos&&first.find("RPM stale")!=std::string::npos);assert(r.evidenceSlot==1);
 r.evidence("worker_exit",false);assert(r.evidenceSlot==1);
 saveText(state+"/worker.result",terminal("invalid/stale RPM"));r.evidence("worker_exit",false);assert(r.evidenceSlot==2);assert(recordTail(root+"/fault-recent-1.json",1000000).find("invalid/stale RPM")!=std::string::npos);
 assert(recordTail(root+"/fault-first.json",1000000)==first);
 unlink((state+"/worker.result").c_str());unlink((state+"/active.jsonl").c_str());assert(!rmdir(state.c_str()));assert(recordTail(root+"/fault-first.json",1000000)==first);
 Resident next(root.c_str(),state.c_str());next.evidence("resident_terminal",true);assert(recordTail(root+"/fault-first.json",1000000)==first);
 Resident unavailable((root+"/missing").c_str(),state.c_str());unavailable.evidence("worker_exit",false);assert(unavailable.lease.failed()&&unavailable.retryAfter==~uint64_t(0));
 for(unsigned i=0;i<4;++i){char p[32];snprintf(p,sizeof(p),"/fault-recent-%u.json",i);unlink((root+p).c_str());}unlink((root+"/fault-first.json").c_str());rmdir(root.c_str());rmdir(tmp);
 puts("Real resident evidence: first preserved, changed reason immediate, repeat throttled, RAM deletion/restart survival, failed storage blocks resume");
}
