```cpp
void Renderer::makeOffscreenTextures(int width, int height) {
    width = std::max(width, 1);
    height = std::max(height, 1);

    MTL::TextureDescriptor* colorDescriptor = MTL::TextureDescriptor::texture2DDescriptor(
        MTL::PixelFormatBGRA8Unorm, width, height, false);
    colorDescriptor->setUsage(MTL::TextureUsageRenderTarget | MTL::TextureUsageShaderRead);
    colorDescriptor->setStorageMode(MTL::StorageModePrivate);
    if (sceneColor) sceneColor->release();
    sceneColor = device->newTexture(colorDescriptor);

    MTL::TextureDescriptor* depthDescriptor = MTL::TextureDescriptor::texture2DDescriptor(
        MTL::PixelFormatDepth32Float, width, height, false);
    depthDescriptor->setUsage(MTL::TextureUsageRenderTarget);
    depthDescriptor->setStorageMode(MTL::StorageModePrivate);
    if (sceneDepth) sceneDepth->release();
    sceneDepth = device->newTexture(depthDescriptor);
}
```

```cpp
MTL::RenderPassDescriptor* scenePass = MTL::RenderPassDescriptor::alloc()->init();
scenePass->colorAttachments()->object(0)->setTexture(sceneColor);
scenePass->colorAttachments()->object(0)->setLoadAction(MTL::LoadActionClear);
scenePass->colorAttachments()->object(0)->setClearColor(MTL::ClearColor::Make(0.1, 0.1, 0.1, 1.0));
scenePass->colorAttachments()->object(0)->setStoreAction(MTL::StoreActionStore);
scenePass->depthAttachment()->setTexture(sceneDepth);
scenePass->depthAttachment()->setLoadAction(MTL::LoadActionClear);
scenePass->depthAttachment()->setClearDepth(1.0);
scenePass->depthAttachment()->setStoreAction(MTL::StoreActionDontCare);
```

```cpp
void Renderer::draw() {
    NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();
    MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();

    // Pass 1: the scene, into our texture.
    MTL::RenderCommandEncoder* sceneEncoder = commandBuffer->renderCommandEncoder(scenePass);
    drawScene(sceneEncoder);
    sceneEncoder->endEncoding();

    // Pass 2: a full-screen triangle, into the drawable.
    if (CA::MetalDrawable* drawable = layer->nextDrawable()) {
        MTL::RenderPassDescriptor* viewPass = MTL::RenderPassDescriptor::alloc()->init();
        viewPass->colorAttachments()->object(0)->setTexture(drawable->texture());
        viewPass->colorAttachments()->object(0)->setLoadAction(MTL::LoadActionDontCare);   // fully overwritten
        viewPass->colorAttachments()->object(0)->setStoreAction(MTL::StoreActionStore);

        MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(viewPass);
        encoder->setRenderPipelineState(postPipelineState);
        encoder->setFragmentTexture(sceneColor, 0);
        encoder->setFragmentSamplerState(samplerState, 0);
        encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(3));
        encoder->endEncoding();

        commandBuffer->presentDrawable(drawable);
        viewPass->release();
    }
    commandBuffer->commit();
    pool->release();
}
```
