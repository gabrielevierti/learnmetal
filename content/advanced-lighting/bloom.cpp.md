```cpp
scenePass->colorAttachments()->object(1)->setTexture(brightTexture);
scenePass->colorAttachments()->object(1)->setLoadAction(MTL::LoadActionClear);
scenePass->colorAttachments()->object(1)->setStoreAction(MTL::StoreActionStore);

pipelineDescriptor->colorAttachments()->object(1)->setPixelFormat(MTL::PixelFormatRGBA16Float);
```

```cpp
MTL::Texture* source = brightTexture;
for (int i = 0; i < 10; i++) {
    bool horizontal = i % 2 == 0;
    MTL::Texture* target = horizontal ? blurTextureA : blurTextureB;

    MTL::RenderPassDescriptor* pass = MTL::RenderPassDescriptor::alloc()->init();
    pass->colorAttachments()->object(0)->setTexture(target);
    pass->colorAttachments()->object(0)->setLoadAction(MTL::LoadActionDontCare);
    pass->colorAttachments()->object(0)->setStoreAction(MTL::StoreActionStore);

    MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(pass);
    encoder->setRenderPipelineState(blurPipelineState);
    BlurUniforms uniforms{horizontal ? simd::float2{1, 0} : simd::float2{0, 1}};
    encoder->setFragmentBytes(&uniforms, sizeof(BlurUniforms), 0);
    encoder->setFragmentTexture(source, 0);
    encoder->setFragmentSamplerState(clampSampler, 0);
    encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(3));
    encoder->endEncoding();
    pass->release();

    source = target;
}
```
