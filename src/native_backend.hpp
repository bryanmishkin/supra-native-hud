#ifndef SUPRA_NATIVE_BACKEND_HPP
#define SUPRA_NATIVE_BACKEND_HPP
#include "hud_core.hpp"
#include "cluster/hudterm.hpp"
#include <vector>
namespace supra {
// No implicit factory handles. This profile must come from verified ownership/geometry.
struct NativeProfile {
    bool mostHudConfirmed, geometryConfirmed, paletteConfirmed, ownershipConfirmed;
    uint16_t host, image[2]; int width,height; unsigned maxItems;
    uint8_t dimColour,tachColour,shiftColour,lineWidth;
    NativeProfile():mostHudConfirmed(false),geometryConfirmed(false),paletteConfirmed(false),ownershipConfirmed(false),host(0),width(0),height(0),maxItems(0),dimColour(0),tachColour(0),shiftColour(0),lineWidth(1) { image[0]=image[1]=0; }
};
struct NativeBatch { std::vector<nbt::hudterm::Call> calls; bool swap; NativeBatch():swap(false){} };
// Split into ordered transport batches, keeping the final swap in the last batch.
// Do not submit stage N+1 until every call in stage N is acknowledged.
bool stageNativeBatch(const NativeBatch&,unsigned maxCalls,std::vector<NativeBatch>&);
// Encoder only. It has no socket, device registration or live send capability.
class NativeBackend {
    NativeProfile profile_; unsigned front_; bool pending_,failed_; NativeBatch pendingBatch_;
    bool profileOk() const;
public:
    explicit NativeBackend(const NativeProfile& p):profile_(p),front_(0),pending_(false),failed_(false){}
    bool prepare(const Update&,bool connected,bool overlayKnown,bool factoryOverlay,NativeBatch&);
    // Call only after every command, including swap, was positively acknowledged.
    void complete(bool allAcknowledged);
    void invalidate() { failed_=true;pending_=false;pendingBatch_=NativeBatch(); }
    bool failed() const { return failed_; }
};
}
#endif
