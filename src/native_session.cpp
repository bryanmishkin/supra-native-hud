#include "native_session.hpp"
#include <string.h>
namespace supra {
using namespace nbt::hudterm;
NativeSession::NativeSession(const NativeProfile& p,uint16_t self,bool tags)
 :backend_(p),profile_(p),self_(self),next_(0),busy_(false),waiting_(false),failed_(false),haveTime_(false),correlationVerified_(tags),lastNow_(0),sentAt_(0),lastSent_(0),frameAt_(0),frameTtl_(0),sentBefore_(false),frameTimed_(false),tag_(1) {
 allowed_.allow(p.image[0]);allowed_.allow(p.image[1]);
}
void NativeSession::fail() { failed_=true;busy_=waiting_=false;batch_=NativeBatch();backend_.invalidate(); }
bool NativeSession::check(uint64_t now,bool permission) {
 if(failed_)return false;
 if(!permission || !correlationVerified_ || !isAppAddress(self_) || (haveTime_ && now<lastNow_)) { fail();return false; }
 haveTime_=true;lastNow_=now;
 // New telemetry does not refresh an older queued frame's expiry.
 if(busy_ && frameTimed_ && (now<frameAt_ || now-frameAt_>frameTtl_)) { fail();return false; }
 if(waiting_ && now-sentAt_>=1500) { fail();return false; }
 return true;
}
bool NativeSession::submit(const Update& u,uint64_t now,bool permission) {
 if(!check(now,permission)||busy_)return false;
 if(u.action==Present && (!u.frame.validForMs || u.frame.validForMs>2000 || now<u.frame.sampleAt || now-u.frame.sampleAt>u.frame.validForMs))return false;
 NativeBatch b;
 if(!backend_.prepare(u,true,true,false,b))return false;
 batch_=b;next_=0;frameTimed_=u.action==Present;frameAt_=u.frame.sampleAt;frameTtl_=u.frame.validForMs;busy_=true;return true;
}
bool NativeSession::next(uint64_t now,bool permission,nbt::most::Msg& out) {
 if(!check(now,permission)||!busy_||waiting_)return false;
 // Conservative test policy: one outstanding call, >=50 ms between calls.
 // This is not a measured vehicle bandwidth budget.
 if(sentBefore_ && now-lastSent_<50)return false;
 if(next_>=batch_.calls.size() || tag_==0) { fail();return false; }
 if(!buildCall(profile_.host,batch_.calls[next_],tag_++,allowed_,inFlight_)) { fail();return false; }
 inFlight_.src=self_;out=inFlight_;waiting_=true;sentAt_=lastSent_=now;sentBefore_=true;return true;
}
void NativeSession::receive(const nbt::most::View& m,uint64_t now,bool permission) {
 if(!check(now,permission)||!waiting_)return;
 if(nbt::most::classify(m)!=nbt::most::kNormal || m.src!=profile_.host || m.dst!=self_
    || m.fblock!=kFBlock || m.inst!=kInst || m.fkt!=inFlight_.fkt || m.hdrTag!=inFlight_.hdrTag)return;
 if(m.op==nbt::most::kOpProcessingAck || m.op==nbt::most::kOpProcessing)return;
 // Only the verified exact-echo success form advances. Unknown response forms fail closed.
 if(m.op!=nbt::most::kOpResultAck || m.len!=inFlight_.data.size() || !m.data
    || memcmp(m.data,&inFlight_.data[0],m.len)) { fail();return; }
 waiting_=false;++next_;
 if(next_==batch_.calls.size()) { backend_.complete(true);batch_=NativeBatch();busy_=false; }
}
}
