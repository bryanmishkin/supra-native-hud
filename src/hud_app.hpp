#ifndef SUPRA_HUD_APP_HPP
#define SUPRA_HUD_APP_HPP
#include "native_session.hpp"
namespace supra {
// Single-threaded orchestration. Caller supplies fresh, timestamped input and owned-profile evidence.
// Does not connect to the car. The transport adapter must serialize all calls to this object.
class HudApp {
    HudCore core_; NativeSession session_; bool stopped_;
    bool allowed(const Input& in) const {
        return !stopped_ && in.connected && in.ownershipConfirmed && in.overlayStateKnown && !in.factoryOverlay;
    }
public:
    HudApp(const Config& c,const NativeProfile& p,uint16_t self,bool verifiedEchoTags)
      :core_(c),session_(p,self,verifiedEchoTags),stopped_(false){}
    bool poll(const Input&,uint64_t now,nbt::most::Msg& out);
    void receive(const Input&,const nbt::most::View&,uint64_t now);
    void stop() { stopped_=true;session_.sendFailed(); }
    void sendFailed() { session_.sendFailed(); }
    bool failed() const { return session_.failed(); }
};
}
#endif
