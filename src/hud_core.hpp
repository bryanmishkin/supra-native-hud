#ifndef SUPRA_HUD_CORE_HPP
#define SUPRA_HUD_CORE_HPP
#include <stdint.h>
namespace supra {
// All timestamps are monotonic milliseconds from one clock. No wall-clock arithmetic.
struct Sample { double value; uint64_t at; bool valid; Sample():value(0),at(0),valid(false){} };
struct Config {
    double maxRpm, shiftRpm; uint64_t staleMs, frameMs;
    bool thresholdsValidated, boostValidated;
    Config():maxRpm(0),shiftRpm(0),staleMs(300),frameMs(100),thresholdsValidated(false),boostValidated(false){}
};
struct Input {
    Sample rpm, manifoldKpa, ambientKpa;
    bool ownershipConfirmed, overlayStateKnown, factoryOverlay, connected;
    Input():ownershipConfirmed(false),overlayStateKnown(false),factoryOverlay(false),connected(false){}
};
struct Segment { double x1,y1,x2,y2; bool lit; };
struct Frame {
    bool visible, boostVisible; double rpm, boostPsi; unsigned shiftLights;
    uint64_t sampleAt, validForMs;
    Segment tach[24];
    Frame():visible(false),boostVisible(false),rpm(0),boostPsi(0),shiftLights(0),sampleAt(0),validForMs(0){}
};
enum Action { NoChange, Present, ClearOwned };
struct Update { Action action; Frame frame; Update():action(NoChange){} };
class HudCore {
    Config config_; bool presented_, haveTime_, haveObserved_, haveSample_; uint64_t last_, observed_, sampleAt_;
public:
    explicit HudCore(const Config& c):config_(c),presented_(false),haveTime_(false),haveObserved_(false),haveSample_(false),last_(0),observed_(0),sampleAt_(0){}
    // Check safety without consuming presentation cadence on an acknowledgement.
    bool canPresent(const Input&,uint64_t now) const;
    bool observe(const Input&,uint64_t now);
    Update update(const Input&,uint64_t now);
};
}
#endif
