// No sockets, worker execution or HUD commands. Uses the production evidence writer.
#define SUPRA_RESIDENT_NO_MAIN
#include "supra_resident.cpp"
int main(int argc,char** argv){
 if(argc!=2)return 64;std::string root=argv[1];
 if(root.compare(0,31,"/var/opt/supra-hud/fault-proof-")!=0)return 64;
 if(mkdir(root.c_str(),0700)||!privateDir(root))return 2;
 std::string state=root+"/fixture";if(mkdir(state.c_str(),0700))return 2;
 try{Resident r(root.c_str(),state.c_str());r.cleanupProven=true;r.lastWaitStatus=512;
  saveText(state+"/worker.result","{\"reason\":\"proof-only-no-vehicle-fault\",\"frames\":0,\"cleanup_verified\":true,\"factory_activity\":false,\"monitor_unknown\":false,\"automatic_resume\":false,\"shared_instance_preserved\":true}\n");
  saveText(state+"/active.jsonl","{\"proof_only\":true,\"hud_writes\":0}\n");
  r.evidence("on_target_storage_proof",true);if(r.lease.failed())return 2;
  std::string first=recordTail(root+"/fault-first.json",1000000);if(first.find("proof-only-no-vehicle-fault")==std::string::npos)return 2;
  unlink((state+"/worker.result").c_str());unlink((state+"/active.jsonl").c_str());rmdir(state.c_str());
  if(recordTail(root+"/fault-first.json",1000000)!=first)return 2;
  puts("PERSISTENT_RECORD_VERIFIED; no vehicle commands; retained for restart readback");return 0;
 }catch(const std::exception& e){fprintf(stderr,"proof: %s\n",e.what());return 2;}
}
