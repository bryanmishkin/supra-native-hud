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
// Passive DisplaySink layouts only. Raw fields have no ownership/geometry meaning.
struct DisplaySinkMessage {
    enum Layout { Unknown, SwitchRequested, SwitchCompleted } layout;
    uint32_t firstFieldHigh, firstFieldLow;
    uint16_t pair[2];
    uint8_t finalField, completion[2];
    DisplaySinkMessage();
};
bool decodeDisplaySink(uint16_t service, uint16_t method, uint8_t interfaceVersion,
                       uint8_t messageType, uint8_t returnCode,
                       const uint8_t *body, size_t bytes, DisplaySinkMessage &out);
}
#endif
