```cpp
MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::textureCubeDescriptor(
    MTL::PixelFormatRGBA16Float, 128, true);                    // true: allocate the mip chain
descriptor->setUsage(MTL::TextureUsageRenderTarget | MTL::TextureUsageShaderRead);
prefilterMap = device->newTexture(descriptor);

const int mipCount = 5;
for (int mip = 0; mip < mipCount; mip++) {
    PrefilterUniforms uniforms{float(mip) / float(mipCount - 1)};
    renderToCube(prefilterMap, mip, commandBuffer,
                 [&](MTL::RenderCommandEncoder* encoder, simd::float4x4 viewProjection) {
        encoder->setRenderPipelineState(prefilterPipelineState);
        encoder->setFragmentBytes(&uniforms, sizeof(PrefilterUniforms), 0);
        encoder->setFragmentTexture(environmentCube, 0);
        encoder->setFragmentSamplerState(trilinearSampler, 0);
        drawCube(encoder, viewProjection);
    });
}
```
