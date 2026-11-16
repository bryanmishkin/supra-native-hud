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
}
