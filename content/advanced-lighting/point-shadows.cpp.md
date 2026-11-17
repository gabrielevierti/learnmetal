```cpp
const NS::UInteger size = 1024;
MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::textureCubeDescriptor(
    MTL::PixelFormatDepth32Float, size, false);
descriptor->setUsage(MTL::TextureUsageRenderTarget | MTL::TextureUsageShaderRead);
descriptor->setStorageMode(MTL::StorageModePrivate);
shadowCube = device->newTexture(descriptor);
```

```cpp
const float farPlane = 25.0f;
simd::float4x4 projection = perspectiveLH(float(M_PI) / 2, 1.0f, 0.1f, farPlane);

struct CubeFace { simd::float3 direction, up; };
const CubeFace faces[6] = {
    {{ 1,  0,  0}, {0, 1,  0}},
    {{-1,  0,  0}, {0, 1,  0}},
    {{ 0,  1,  0}, {0, 0, -1}},
    {{ 0, -1,  0}, {0, 0,  1}},
    {{ 0,  0,  1}, {0, 1,  0}},
    {{ 0,  0, -1}, {0, 1,  0}},
};

simd::float4x4 faceMatrices[6];
for (int i = 0; i < 6; i++) {
    faceMatrices[i] = projection * lookAtLH(lightPosition, lightPosition + faces[i].direction, faces[i].up);
}
```

```cpp
for (int face = 0; face < 6; face++) {
    MTL::RenderPassDescriptor* pass = MTL::RenderPassDescriptor::alloc()->init();
    pass->depthAttachment()->setTexture(shadowCube);
    pass->depthAttachment()->setSlice(face);
    pass->depthAttachment()->setLoadAction(MTL::LoadActionClear);
    pass->depthAttachment()->setClearDepth(1.0);
    pass->depthAttachment()->setStoreAction(MTL::StoreActionStore);

    MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(pass);
    encoder->setRenderPipelineState(pointShadowPipelineState);
    encoder->setDepthStencilState(depthState);
    encoder->setFrontFacingWinding(MTL::WindingClockwise);      // the left-handed view mirrors the scene
    PointShadowUniforms uniforms{faceMatrices[face], lightPosition, farPlane};
    drawScene(encoder, uniforms);
    encoder->endEncoding();
    pass->release();
}
```
