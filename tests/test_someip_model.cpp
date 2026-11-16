#include "someip_model.hpp"
#include <assert.h>
#include <string.h>
using namespace supra;
int main() {
    // Synthetic envelope; no factory payload or route data in source tests.
    uint8_t b[26]={0,0,0,7,0,0,0,9,46,0,0,0,9,0,0,0,3,0,0,0,9,46,0,0,0,8};
    ModelRequest out;
    assert(decodeObservedModel(0xb00e,9,b,sizeof(b),out));
    assert(out.layout==ModelRequest::ModelUpdate && out.handle==7 && out.modelId==9 && out.modelType==46 && out.tag==3 && out.payloadBytes==9);
    for(size_t n=0;n<sizeof(b);++n) assert(!decodeObservedModel(0xb00e,9,b,n,out));
    assert(!decodeObservedModel(0xb00e,9,0,26,out));
    assert(!decodeObservedModel(0xb006,9,b,26,out));
    assert(!decodeObservedModel(0xb00e,1,b,26,out));
    b[12]=8;assert(!decodeObservedModel(0xb00e,9,b,26,out));b[12]=9;
    b[20]=10;assert(!decodeObservedModel(0xb00e,9,b,26,out));b[20]=9;
    b[21]=45;assert(!decodeObservedModel(0xb00e,9,b,26,out));b[21]=46;
    assert(out.layout==ModelRequest::Unknown && out.payload==0);
    assert(decodeObservedModel(0xb00e,4,b,4,out));
    b[8]=3;assert(decodeObservedModel(0xb006,2,b,9,out));
    assert(out.layout==ModelRequest::ModelReference);
    return 0;
}
