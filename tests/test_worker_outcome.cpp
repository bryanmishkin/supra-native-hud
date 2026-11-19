#include "worker_outcome.hpp"
#include "fault_record.hpp"
#include "factory_rpm.hpp"
#include "tach_bitmap.hpp"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <iostream>
using namespace supra;
static std::string result(const char* why,bool clean=true){return std::string("{\"reason\":\"")+why+"\",\"frames\":17,\"cleanup_verified\":"+(clean?"true":"false")+",\"factory_activity\":false,\"monitor_unknown\":false,\"automatic_resume\":false,\"shared_instance_preserved\":true}\n";}
int main(){
 WorkerOutcome o=workerOutcome(result("RPM stale"));assert(o.valid&&inputRecovery(o));
 assert(inputRecovery(workerOutcome(result("invalid/stale RPM"))));
 assert(inputRecovery(workerOutcome(result("rpm_transport:factory feed stale"))));
 assert(!inputRecovery(workerOutcome(result("RPM stale",false))));
 assert(!workerOutcome(result("RPM stale")+"junk").valid);
 assert(!workerOutcome("garbage"+result("RPM stale")).valid);
 assert(workerOutcome("[DsiClient] ready\n"+result("RPM stale")).valid);
 assert(!workerOutcome("{\"cleanup_verified\":true}\n").valid);
 o=workerOutcome(result("factory_activity_quiesced"));assert(o.valid&&!inputRecovery(o));assert(std::string(unexpectedExit(o,true))=="worker unexpected clean exit");
 o=workerOutcome(result("monitor_unknown_quiesced"));assert(!inputRecovery(o));
 assert(std::string(unexpectedExit(o,false))=="worker terminated by signal");
 assert(!inputRecovery(workerOutcome(result("I/O deadline"))));
 o=workerOutcome(result("bitmap pool in use"));assert(!poolRecovery(o));o.frames=0;assert(poolRecovery(o));o.clean=false;assert(!poolRecovery(o));o.clean=true;o.unknown=true;assert(!poolRecovery(o));o.unknown=false;o.foreign=true;assert(!poolRecovery(o));
 o=workerOutcome("{\"reason\":\"factory_activity_quiesced\",\"frames\":0,\"cleanup_verified\":true,\"factory_activity\":true,\"monitor_unknown\":false,\"automatic_resume\":false,\"shared_instance_preserved\":true}\n");
 assert(factoryAdmissionRecovery(o));
 o.frames=1;assert(!factoryAdmissionRecovery(o));o.frames=0;
 o.clean=false;assert(!factoryAdmissionRecovery(o));o.clean=true;
 o.unknown=true;assert(!factoryAdmissionRecovery(o));o.unknown=false;
 o.foreign=false;assert(!factoryAdmissionRecovery(o));o.foreign=true;
 o.valid=false;assert(!factoryAdmissionRecovery(o));o.valid=true;
 o.reason="I/O deadline";assert(!factoryAdmissionRecovery(o));
 nbt::most::View v;memset(&v,0,sizeof(v));unsigned char raw[2];v.varTag=2;v.src=0x5000;v.dst=0x205e;v.fblock=5;v.fkt=0xcd0;v.op=12;v.data=raw;v.len=2;
 unsigned values[]={650,6500,7000,1000,7700,0,6900,3000,7500};Config c;c.maxRpm=7000;c.shiftRpm=6500;c.thresholdsValidated=true;HudCore core(c);
 for(unsigned i=0;i<sizeof(values)/sizeof(values[0]);++i){unsigned n=values[i]*4;raw[0]=n>>8;raw[1]=n;Sample sample;assert(decodeFactoryRpm(v,0x205e,1000+i*1000,sample)&&sample.valid);Input in;in.connected=in.ownershipConfirmed=in.overlayStateKnown=true;in.rpm=sample;Update u=core.update(in,sample.at);assert(u.action==Present&&u.frame.rpm==values[i]);assert(!tachBitmapSport(u.frame).empty());}
 raw[0]=30801>>8;raw[1]=30801&255;Sample s;assert(decodeFactoryRpm(v,0x205e,20000,s)&&!s.valid);
 char dir[]="/tmp/supra-fault-test-XXXXXX";assert(mkdtemp(dir));std::string p=std::string(dir)+"/record.json";
 std::string body="{\"result\":"+jsonString(result("RPM stale"))+"}\n";assert(durableRecord(p,body));assert(recordTail(p,65536)==body);assert(recordTail(p,2)=="}\n");
 assert(!durableRecord(std::string(dir)+"/missing/record.json",body));assert(recordTail(p,65536)==body);unlink(p.c_str());rmdir(dir);
 std::cout<<"Strict exit classification, durable record failure handling and rapid/boundary RPM rendering passed\n";
}
