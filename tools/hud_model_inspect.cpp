// Offline SOME/IP stream inspection. Input must already be reassembled and message aligned.
#include "someip_model.hpp"
#include <iostream>
#include <stdint.h>
static unsigned u16(const uint8_t *p) {return (unsigned(p[0])<<8)|p[1];}
static uint32_t u32(const uint8_t *p) {return (uint32_t(p[0])<<24)|(uint32_t(p[1])<<16)|(uint32_t(p[2])<<8)|p[3];}
int main() {
    uint8_t header[16],body[65536];size_t total=0,count=0;
    while(true) {
        std::cin.read(reinterpret_cast<char *>(header),16);
        if(std::cin.gcount()==0 && std::cin.eof()) return 0;
        if(std::cin.gcount()!=16 || header[12]!=1) return 2;
        const uint32_t length=u32(header+4);
        if(length<8 || length-8>sizeof(body) || ++count>65536) return 2;
        total+=length+8;if(total>16*1024*1024) return 2;
        const size_t bytes=length-8;
        std::cin.read(reinterpret_cast<char *>(body),bytes);
        if(size_t(std::cin.gcount())!=bytes) return 2;
        supra::ModelRequest out;
        const bool accepted=header[14]==0 && supra::decodeObservedModel(u16(header),u16(header+2),body,bytes,out);
        std::cout<<"{\"service\":"<<u16(header)<<",\"method\":"<<u16(header+2)
                 <<",\"message_type\":"<<unsigned(header[14])<<",\"decoded\":"<<(accepted?"true":"false")
                 <<",\"layout\":"<<out.layout<<",\"handle\":"<<out.handle<<",\"model_id\":"<<out.modelId
                 <<",\"model_type\":"<<unsigned(out.modelType)<<",\"tag\":"<<out.tag
                 <<",\"payload_bytes\":"<<out.payloadBytes<<",\"drawing_authorized\":false}\n";
        if(!std::cout) return 2;
    }
}
