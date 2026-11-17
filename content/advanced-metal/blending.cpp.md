```cpp
MTL::RenderPipelineColorAttachmentDescriptor* attachment = pipelineDescriptor->colorAttachments()->object(0);
attachment->setBlendingEnabled(true);
attachment->setRgbBlendOperation(MTL::BlendOperationAdd);
attachment->setAlphaBlendOperation(MTL::BlendOperationAdd);
attachment->setSourceRGBBlendFactor(MTL::BlendFactorSourceAlpha);
attachment->setDestinationRGBBlendFactor(MTL::BlendFactorOneMinusSourceAlpha);
attachment->setSourceAlphaBlendFactor(MTL::BlendFactorOne);
attachment->setDestinationAlphaBlendFactor(MTL::BlendFactorOneMinusSourceAlpha);
```

```cpp
std::vector<simd::float3> sortedWindows = windowPositions;
std::sort(sortedWindows.begin(), sortedWindows.end(), [&](simd::float3 a, simd::float3 b) {
    return simd::distance_squared(camera.position, a) > simd::distance_squared(camera.position, b);
});

encoder->setRenderPipelineState(blendPipelineState);
encoder->setDepthStencilState(depthTestNoWriteState);
for (simd::float3 position : sortedWindows) {
    uniforms.model = translation(position);
    encoder->setVertexBytes(&uniforms, sizeof(Uniforms), 1);
    encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(6));
}
```
