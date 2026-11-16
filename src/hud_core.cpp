#include "hud_core.hpp"
namespace supra {
static bool bounded(double v,double low,double high) { return v>=low && v<=high; }
static bool fresh(const Sample& s,uint64_t now,uint64_t ttl) {
    return s.valid && s.at<=now && now-s.at<=ttl;
}
bool HudCore::canPresent(const Input& in,uint64_t now) const {
    bool clockOk=!haveObserved_ || now>=observed_;
    bool configOk=config_.thresholdsValidated && bounded(config_.maxRpm,1,20000)
        && bounded(config_.shiftRpm,1,config_.maxRpm) && config_.staleMs>0 && config_.staleMs<=2000
        && config_.frameMs>=100 && config_.frameMs<=1000;
    return clockOk && configOk && in.connected && in.ownershipConfirmed
        && in.overlayStateKnown && !in.factoryOverlay && fresh(in.rpm,now,config_.staleMs)
        && (!haveSample_ || in.rpm.at>=sampleAt_)
        && bounded(in.rpm.value,0,config_.maxRpm*1.1);
}
bool HudCore::observe(const Input& in,uint64_t now) {
    bool valid=canPresent(in,now);
    haveObserved_=true;observed_=now;
    if(valid) {haveSample_=true;sampleAt_=in.rpm.at;}
    return valid;
}
Update HudCore::update(const Input& in,uint64_t now) {
    Update u;
    bool show=observe(in,now);
    if(!show) {
        if(presented_)u.action=ClearOwned;
        presented_=false;
        // Reset cadence on suppression; a clock rollback never keeps an old display alive.
        haveTime_=false;return u;
    }
    if(haveTime_ && now-last_<config_.frameMs)return u;
    haveTime_=true;last_=now;presented_=true;u.action=Present;
    Frame& f=u.frame;f.visible=true;f.rpm=in.rpm.value;f.sampleAt=in.rpm.at;f.validForMs=config_.staleMs;
    double fraction=in.rpm.value/config_.maxRpm;if(fraction>1)fraction=1;
    for(unsigned i=0;i<24;++i) {
        double x=0.06+0.88*i/24.0, next=0.06+0.88*(i+0.85)/24.0;
        // Normalized upper arc: native placement is supplied only after geometry validation.
        f.tach[i].x1=x;f.tach[i].x2=next;
        f.tach[i].y1=0.12+0.28*(x-0.5)*(x-0.5);
        f.tach[i].y2=0.12+0.28*(next-0.5)*(next-0.5);
        f.tach[i].lit=fraction>=(i+1)/24.0;
    }
    double start=config_.shiftRpm*0.8;
    if(in.rpm.value>=config_.shiftRpm)f.shiftLights=5;
    else if(in.rpm.value>=start)f.shiftLights=1+(unsigned)(4*(in.rpm.value-start)/(config_.shiftRpm-start));
    if(config_.boostValidated && fresh(in.manifoldKpa,now,config_.staleMs)
       && fresh(in.ambientKpa,now,config_.staleMs)
       && bounded(in.manifoldKpa.value,0,400) && bounded(in.ambientKpa.value,50,120)) {
        uint64_t skew=in.manifoldKpa.at>in.ambientKpa.at?in.manifoldKpa.at-in.ambientKpa.at:in.ambientKpa.at-in.manifoldKpa.at;
        if(skew<=100) { f.boostVisible=true;f.boostPsi=(in.manifoldKpa.value-in.ambientKpa.value)*0.1450377377; }
    }
    return u;
}
}
