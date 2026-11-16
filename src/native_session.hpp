#ifndef SUPRA_NATIVE_SESSION_HPP
#define SUPRA_NATIVE_SESSION_HPP
#include "native_backend.hpp"
namespace supra {
// Host-testable sender state machine. No I/O, allocation of native objects or device registration.
class NativeSession {
    NativeBackend backend_; NativeProfile profile_; uint16_t self_;
    nbt::hudterm::HandleSet allowed_; NativeBatch batch_; size_t next_;
    bool busy_,waiting_,failed_,haveTime_,correlationVerified_;
    uint64_t lastNow_,sentAt_,lastSent_,frameAt_,frameTtl_; bool sentBefore_,frameTimed_;
    uint32_t tag_; nbt::most::Msg inFlight_;
    bool check(uint64_t now,bool permission);
    void fail();
public:
    NativeSession(const NativeProfile&,uint16_t self,bool verifiedEchoTags);
    bool submit(const Update&,uint64_t now,bool permission);
    bool next(uint64_t now,bool permission,nbt::most::Msg& out);
    void receive(const nbt::most::View&,uint64_t now,bool permission);
    void tick(uint64_t now,bool permission) { check(now,permission); }
    void sendFailed() { fail(); }
    bool busy() const { return busy_; }
    bool failed() const { return failed_; }
};
}
#endif
