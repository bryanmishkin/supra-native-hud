#include "native_backend.hpp"
namespace supra {
using namespace nbt::hudterm;
bool stageNativeBatch(const NativeBatch& source,unsigned limit,std::vector<NativeBatch>& out) {
    out.clear();
    if(!limit || limit>32 || source.calls.empty() || source.calls.size()>48)return false;
    for(size_t i=0;i<source.calls.size();++i) {
        if(source.calls[i].fkt==kSwitchVisibility && i+1!=source.calls.size())return false;
        if(!payloadShapeOk(source.calls[i].fkt,source.calls[i].payload))return false;
    }
    for(size_t i=0;i<source.calls.size();++i) {
        if(i%limit==0)out.push_back(NativeBatch());
        out.back().calls.push_back(source.calls[i]);
    }
    out.back().swap=source.swap;
    return true;
}
bool NativeBackend::profileOk() const {
    return profile_.mostHudConfirmed && profile_.geometryConfirmed && profile_.paletteConfirmed
      && profile_.ownershipConfirmed && isRingNode(profile_.host)
      && profile_.image[0]>0 && profile_.image[0]<=kMaxHandle
      && profile_.image[1]>0 && profile_.image[1]<=kMaxHandle && profile_.image[0]!=profile_.image[1]
      && profile_.width>=32 && profile_.width<=32767 && profile_.height>=32 && profile_.height<=32767
      && profile_.maxItems>=29 && profile_.lineWidth>0 && profile_.lineWidth<=16;
}
static bool unit(double x) { return x>=0 && x<=1; }
static int16_t coord(double x,int size) { return (int16_t)(x*(size-1)+0.5); }
static void add(NativeBatch& b,uint16_t id,const std::vector<uint8_t>& p) { b.calls.push_back(Call(id,p)); }
bool NativeBackend::prepare(const Update& u,bool connected,bool known,bool overlay,NativeBatch& out) {
    out=NativeBatch();
    // Any loss of permission invalidates the session, including an in-flight batch.
    // Sender must cancel queued work; recovery requires a freshly verified profile.
    if(!connected || !known || overlay) { invalidate();return false; }
    if(failed_ || pending_ || !profileOk() || u.action==NoChange)return false;
    NativeBatch b;
    if(u.action==ClearOwned) {
        add(b,kSetVisibility,setVisibility(profile_.image[0],false));
        add(b,kSetVisibility,setVisibility(profile_.image[1],false));
    } else if(u.action==Present && u.frame.visible && u.frame.shiftLights<=5) {
        for(unsigned i=0;i<24;++i) {
            const Segment& s=u.frame.tach[i];
            if(!unit(s.x1)||!unit(s.x2)||!unit(s.y1)||!unit(s.y2))return false;
        }
        uint16_t back=profile_.image[1-front_];
        add(b,kSetVisibility,setVisibility(back,false));
        add(b,kRemoveAllItems,removeAllItems(back));
        add(b,kSetLineWidth,setLineWidth(back,profile_.lineWidth));
        unsigned index=0;
        for(unsigned pass=0;pass<2;++pass) {
            add(b,kSetLineColor,setLineColor(back,pass?profile_.tachColour:profile_.dimColour));
            for(unsigned i=0;i<24;++i)if(u.frame.tach[i].lit==(pass!=0)) {
                const Segment& s=u.frame.tach[i];std::vector<Point> points(2);
                points[0].x=coord(s.x1,profile_.width);points[0].y=coord(s.y1,profile_.height);
                points[1].x=coord(s.x2,profile_.width);points[1].y=coord(s.y2,profile_.height);
                add(b,kAddPolygon,addPolygon(back,index++,kPolyline,points));
            }
        }
        for(unsigned i=0;i<5;++i) {
            add(b,kSetLineColor,setLineColor(back,i<u.frame.shiftLights?profile_.shiftColour:profile_.dimColour));
            std::vector<Point> points(2);
            points[0].x=coord(0.34+i*0.065,profile_.width);points[1].x=coord(0.38+i*0.065,profile_.width);
            points[0].y=points[1].y=coord(0.27,profile_.height);
            add(b,kAddPolygon,addPolygon(back,index++,kPolyline,points));
        }
        add(b,kSwitchVisibility,switchVisibility(profile_.image[front_],back));b.swap=true;
    } else return false;
    // Validate the complete plan before exposing any command to the caller.
    if(b.calls.size()>48)return false;
    for(size_t i=0;i<b.calls.size();++i) {
        const Call& call=b.calls[i];
        if(!payloadShapeOk(call.fkt,call.payload))return false;
        uint16_t handle=rdBe16(&call.payload[0]);
        if(handle!=profile_.image[0]&&handle!=profile_.image[1])return false;
    }
    pending_=true;pendingBatch_=b;out=b;return true;
}
void NativeBackend::complete(bool acknowledged) {
    if(!pending_)return;
    if(!acknowledged)failed_=true;
    else if(pendingBatch_.swap)front_=1-front_;
    pending_=false;pendingBatch_=NativeBatch();
}
}
