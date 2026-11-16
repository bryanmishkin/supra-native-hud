#include "hud_app.hpp"
namespace supra {
bool HudApp::poll(const Input& in,uint64_t now,nbt::most::Msg& out) {
    bool permission=allowed(in);
    Update u=core_.update(in,now);
    // Never finish an in-flight draw after its input became stale/invalid.
    // Cancellation may leave remote state ambiguous: require reacquisition, not automatic retry.
    if(u.action==ClearOwned && session_.busy()) { session_.sendFailed();return false; }
    session_.tick(now,permission);
    if(session_.failed())return false;
    if(!session_.busy() && u.action!=NoChange)session_.submit(u,now,permission);
    return session_.next(now,permission,out);
}
void HudApp::receive(const Input& in,const nbt::most::View& msg,uint64_t now) {
    // A reply must not advance the frame clock and discard a pending presentation.
    if(!core_.observe(in,now) && session_.busy()) { session_.sendFailed();return; }
    session_.receive(msg,now,allowed(in));
}
}
