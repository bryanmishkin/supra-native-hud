#ifndef SUPRA_SOMEIP_MODEL_HPP
#define SUPRA_SOMEIP_MODEL_HPP
#include <stddef.h>
#include <stdint.h>
namespace supra {
// Observed request-body layouts only. Does not allocate, transmit or establish ownership.
struct ModelRequest {
    enum Layout { Unknown, HandleOnly, ModelReference, ModelUpdate } layout;
    uint32_t handle, modelId, tag;
    uint8_t modelType;
    const uint8_t *payload;
    size_t payloadBytes;
    ModelRequest();
};
bool decodeObservedModel(uint16_t service, uint16_t method,
                         const uint8_t *body, size_t bytes, ModelRequest &out);
}
#endif
