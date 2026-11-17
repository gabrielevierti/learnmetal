```cpp
void Renderer::draw() {
    NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();
    CA::MetalDrawable* drawable = layer->nextDrawable();
    if (drawable) {
        MTL::RenderPassDescriptor* passDescriptor = makePassDescriptor(drawable->texture());
        MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();
        MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(passDescriptor);

        encoder->setRenderPipelineState(pipelineState);
        encoder->setDepthStencilState(depthState);
        encoder->setVertexBuffer(vertexBuffer, 0, 0);
        encoder->setVertexBytes(&uniforms, sizeof(Uniforms), 1);
        encoder->setFragmentTexture(texture, 0);
        encoder->setFragmentSamplerState(samplerState, 0);
        encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(36));

        encoder->endEncoding();
        commandBuffer->presentDrawable(drawable);
        commandBuffer->commit();
        passDescriptor->release();
    }
    pool->release();
}
```
