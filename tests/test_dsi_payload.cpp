#include "dsi_payload.hpp"
#include <assert.h>
#include <stdio.h>
int main() {
 unsigned char data=0;
 assert(nbt::validIpcPayload(32,6,0,0,&data));
 assert(nbt::validIpcPayload(0,0,0,0,0));
 assert(!nbt::validIpcPayload(32,33,0,0,&data));
 assert(!nbt::validIpcPayload(32,6,16,0,&data));
 assert(!nbt::validIpcPayload(32,6,0,1,&data));
 assert(!nbt::validIpcPayload(32,6,0,0,0));
 assert(!nbt::validIpcPayload(0xffffffffu,65537,0,0,&data));
 assert(!nbt::validIpcPayload(0xffffffffu,0xffffffffu,0,0,&data));
 puts("PASS: DSI payload guard rejects alternate layout, error, null, oversized and inconsistent buffers");
}
