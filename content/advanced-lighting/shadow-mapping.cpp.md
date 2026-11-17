```cpp
const NS::UInteger shadowSize = 2048;
MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
    MTL::PixelFormatDepth32Float, shadowSize, shadowSize, false);
descriptor->setUsage(MTL::TextureUsageRenderTarget | MTL::TextureUsageShaderRead);
descriptor->setStorageMode(MTL::StorageModePrivate);
shadowMap = device->newTexture(descriptor);

shadowPass = MTL::RenderPassDescriptor::alloc()->init();
shadowPass->depthAttachment()->setTexture(shadowMap);
shadowPass->depthAttachment()->setLoadAction(MTL::LoadActionClear);
shadowPass->depthAttachment()->setClearDepth(1.0);
shadowPass->depthAttachment()->setStoreAction(MTL::StoreActionStore);
```

```cpp
/// Right-handed orthographic projection with a 0...1 depth range.
inline simd::float4x4 orthographic(float l, float r, float b, float t, float n, float f) {
    return simd_matrix(simd_make_float4(2 / (r - l), 0, 0, 0),
                       simd_make_float4(0, 2 / (t - b), 0, 0),
                       simd_make_float4(0, 0, 1 / (n - f), 0),
                       simd_make_float4((l + r) / (l - r), (t + b) / (b - t), n / (n - f), 1));
}
```

```cpp
simd::float3 lightPosition = {-2, 4, -1};
simd::float4x4 lightView = lookAt(lightPosition, simd::float3{0, 0, 0}, simd::float3{0, 1, 0});
simd::float4x4 lightProjection = orthographic(-10, 10, -10, 10, 1, 12);
simd::float4x4 lightViewProjection = lightProjection * lightView;
```

```cpp
MTL::RenderPipelineDescriptor* descriptor = MTL::RenderPipelineDescriptor::alloc()->init();
descriptor->setVertexFunction(library->newFunction(MTLSTR("vertex_shadow")));
descriptor->setFragmentFunction(nullptr);
descriptor->setVertexDescriptor(vertexDescriptor);
descriptor->setDepthAttachmentPixelFormat(MTL::PixelFormatDepth32Float);
shadowPipelineState = device->newRenderPipelineState(descriptor, &error);
```

```cpp
MTL::SamplerDescriptor* shadowSamplerDescriptor = MTL::SamplerDescriptor::alloc()->init();
shadowSamplerDescriptor->setMinFilter(MTL::SamplerMinMagFilterLinear);
shadowSamplerDescriptor->setMagFilter(MTL::SamplerMinMagFilterLinear);
shadowSamplerDescriptor->setCompareFunction(MTL::CompareFunctionLessEqual);
shadowSamplerDescriptor->setSAddressMode(MTL::SamplerAddressModeClampToEdge);
shadowSamplerDescriptor->setTAddressMode(MTL::SamplerAddressModeClampToEdge);
shadowSampler = device->newSamplerState(shadowSamplerDescriptor);
```

```cpp
shadowEncoder->setDepthBias(0.015f, 7.0f, 0.02f);      // bias, slope scale, clamp
```
