```cpp
MTL::MeshRenderPipelineDescriptor* descriptor = MTL::MeshRenderPipelineDescriptor::alloc()->init();
descriptor->setMeshFunction(library->newFunction(MTLSTR("mesh_main")));
descriptor->setFragmentFunction(library->newFunction(MTLSTR("fragment_main")));
descriptor->colorAttachments()->object(0)->setPixelFormat(MTL::PixelFormatBGRA8Unorm);
descriptor->setDepthAttachmentPixelFormat(MTL::PixelFormatDepth32Float);

NS::Error* error = nullptr;
MTL::RenderPipelineState* pipelineState =
    device->newRenderPipelineState(descriptor, MTL::PipelineOptionNone, nullptr, &error);
descriptor->release();
```

```cpp
encoder->setRenderPipelineState(pipelineState);
encoder->setMeshBuffer(uniformBuffer, 0, 0);
encoder->drawMeshThreadgroups(
    MTL::Size(32, 32, 1),                 // 1,024 quads
    MTL::Size(1, 1, 1),                   // threads per object threadgroup
    MTL::Size(4, 1, 1));                  // threads per mesh threadgroup
```
