```cpp
MTL::Buffer* buffer = device->newBuffer(1024, MTL::ResourceStorageModeShared);
```

```cpp
Uniforms* pointer = static_cast<Uniforms*>(buffer->contents());
*pointer = uniforms;
```

```cpp
std::memcpy(buffer->contents(), vertices.data(), sizeof(Vertex) * vertices.size());
```

```cpp
#include <dispatch/dispatch.h>

static const int maxFramesInFlight = 3;
dispatch_semaphore_t frameSemaphore = dispatch_semaphore_create(maxFramesInFlight);
MTL::Buffer* uniformBuffers[maxFramesInFlight];
int frameIndex = 0;

// constructor
for (int i = 0; i < maxFramesInFlight; i++) {
    uniformBuffers[i] = device->newBuffer(sizeof(Uniforms) * maxObjects, MTL::ResourceStorageModeShared);
}
```

```cpp
void Renderer::draw() {
    dispatch_semaphore_wait(frameSemaphore, DISPATCH_TIME_FOREVER);
    frameIndex = (frameIndex + 1) % maxFramesInFlight;
    MTL::Buffer* uniformBuffer = uniformBuffers[frameIndex];

    MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();
    dispatch_semaphore_t semaphore = frameSemaphore;
    commandBuffer->addCompletedHandler([semaphore](MTL::CommandBuffer*) {
        dispatch_semaphore_signal(semaphore);
    });

    // Write all objects' uniforms into the buffer...
    Uniforms* uniformsPointer = static_cast<Uniforms*>(uniformBuffer->contents());
    for (size_t i = 0; i < objects.size(); i++) {
        uniformsPointer[i] = objects[i].uniforms;
    }

    // ...then bind once and move the offset per draw.
    encoder->setVertexBuffer(uniformBuffer, 0, 1);
    for (size_t i = 0; i < objects.size(); i++) {
        encoder->setVertexBufferOffset(sizeof(Uniforms) * i, 1);
        // draw object i
    }
    // ...
}
```

```cpp
MTL::BlitCommandEncoder* blit = commandBuffer->blitCommandEncoder();

// Buffer to buffer
blit->copyFromBuffer(sourceBuffer, 0, destinationBuffer, 0, sourceBuffer->length());

// Texture to texture (same format and size)
blit->copyFromTexture(sourceTexture, destinationTexture);

// Build the mipmap chain of a texture you rendered or filled yourself
blit->generateMipmaps(texture);

blit->endEncoding();
```

```cpp
NS::UInteger bytesPerRow = texture->width() * 4;
MTL::Buffer* readback = device->newBuffer(bytesPerRow * texture->height(), MTL::ResourceStorageModeShared);

MTL::BlitCommandEncoder* blit = commandBuffer->blitCommandEncoder();
blit->copyFromTexture(texture, 0, 0,                                        // slice, level
                      MTL::Origin::Make(0, 0, 0),
                      MTL::Size::Make(texture->width(), texture->height(), 1),
                      readback, 0,                                          // destination, offset
                      bytesPerRow,
                      bytesPerRow * texture->height());
blit->endEncoding();

commandBuffer->addCompletedHandler([readback](MTL::CommandBuffer*) {
    void* pixels = readback->contents();   // valid now
});
commandBuffer->commit();
```
