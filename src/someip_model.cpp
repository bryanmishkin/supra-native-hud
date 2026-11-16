#include "someip_model.hpp"
namespace supra {
ModelRequest::ModelRequest():layout(Unknown),handle(0),modelId(0),tag(0),modelType(0),payload(0),payloadBytes(0){}
static uint32_t u32(const uint8_t *p) {
    return (uint32_t(p[0])<<24)|(uint32_t(p[1])<<16)|(uint32_t(p[2])<<8)|uint32_t(p[3]);
}
bool decodeObservedModel(uint16_t service,uint16_t method,const uint8_t *b,size_t n,ModelRequest &out) {
    out=ModelRequest();
    if(!b || n<4 || n>65536) return false;
    ModelRequest value;
    value.handle=u32(b);
    // Handle values are recorded, never treated as app-owned or stable across boots.
    if(service==0xb00e && method==4 && n==4) {
        value.layout=ModelRequest::HandleOnly;out=value;return true;
    }
    if(service==0xb006 && method==2 && n==9 && b[8]==3) {
        value.layout=ModelRequest::ModelReference;
        value.modelId=u32(b+4);value.modelType=b[8];out=value;return true;
    }
    if(n<22) return false;
    const uint8_t type=b[8];
    bool known=(service==0xb006 && ((method==9 && (type==17 || type==33)) ||
                (method==3 && type==3) || (method==14 && type==40))) ||
               (service==0xb00e && ((method==11 && type==28) || (method==9 && type==46)));
    if(!known || u32(b+9)!=n-17 || u32(b+4)!=u32(b+17) || type!=b[21]) return false;
    value.layout=ModelRequest::ModelUpdate;value.modelId=u32(b+4);value.modelType=type;
    value.tag=u32(b+13);value.payload=b+17;value.payloadBytes=n-17;
    out=value;return true;
}

DisplaySinkMessage::DisplaySinkMessage():layout(Unknown),firstFieldHigh(0),firstFieldLow(0),finalField(0) {
    pair[0]=pair[1]=0;completion[0]=completion[1]=0;
}
bool decodeDisplaySink(uint16_t service,uint16_t method,uint8_t version,
                       uint8_t kind,uint8_t rc,const uint8_t *b,size_t n,DisplaySinkMessage &out) {
    out=DisplaySinkMessage();
    if(service!=0xb009 || version!=1 || rc!=0 || !b) return false;
    DisplaySinkMessage value;
    if(method==0x8001 && kind==2 && n==13) {
        value.layout=DisplaySinkMessage::SwitchRequested;
        value.firstFieldHigh=u32(b);value.firstFieldLow=u32(b+4);
        value.pair[0]=(uint16_t(b[8])<<8)|b[9];
        value.pair[1]=(uint16_t(b[10])<<8)|b[11];value.finalField=b[12];
    } else if(method==1 && kind==1 && n==2) {
        value.layout=DisplaySinkMessage::SwitchCompleted;
        value.completion[0]=b[0];value.completion[1]=b[1];
    } else return false;
    out=value;return true;
}
}
