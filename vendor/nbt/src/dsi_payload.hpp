#ifndef SUPRA_DSI_PAYLOAD_HPP
#define SUPRA_DSI_PAYLOAD_HPP
#include <stdint.h>
namespace nbt {
// Scalar checks for the audited IPC layout; cannot prove pointer accessibility.
inline bool validIpcPayload(uint32_t capacity,uint32_t length,uint32_t cursor,uint32_t error,const void* data) {
    return !error && !cursor && length<=capacity && length<=65536 && (!length || data);
}
}
#endif
