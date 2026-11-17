```cpp
// Renderer.hpp
#pragma once
#include <Metal/Metal.hpp>
#include <QuartzCore/QuartzCore.hpp>

class Renderer {
public:
    Renderer(MTL::Device* device, CA::MetalLayer* layer);
    ~Renderer();

    // Called when the window is resized. We will need it for the projection matrix later.
    void resize(int width, int height) {}
    void draw();

private:
    MTL::Device* device;
    MTL::CommandQueue* commandQueue;
    CA::MetalLayer* layer;
};

// Renderer.cpp
#include "Renderer.hpp"

Renderer::Renderer(MTL::Device* device, CA::MetalLayer* layer)
    : device(device->retain()), layer(layer) {
    commandQueue = device->newCommandQueue();
    layer->setPixelFormat(MTL::PixelFormatBGRA8Unorm);
}

Renderer::~Renderer() {
    commandQueue->release();
    device->release();
}

void Renderer::draw() {
    // Objects returned by methods that do not start with new/alloc are autoreleased.
    NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();

    CA::MetalDrawable* drawable = layer->nextDrawable();
    if (drawable) {
        // There is no MTKView to hand us a descriptor, so we describe the pass ourselves.
        MTL::RenderPassDescriptor* passDescriptor = MTL::RenderPassDescriptor::alloc()->init();
        MTL::RenderPassColorAttachmentDescriptor* color = passDescriptor->colorAttachments()->object(0);
        color->setTexture(drawable->texture());
        color->setLoadAction(MTL::LoadActionClear);
        color->setClearColor(MTL::ClearColor::Make(0.2, 0.3, 0.3, 1.0));
        color->setStoreAction(MTL::StoreActionStore);

        MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();
        MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(passDescriptor);

        // Draw calls will go here.

        encoder->endEncoding();
        commandBuffer->presentDrawable(drawable);
        commandBuffer->commit();
        passDescriptor->release();
    }
    pool->release();
}
```
