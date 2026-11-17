```cpp
MTL::Buffer* factorBuffer = device->newBuffer(12 * patchCount, MTL::ResourceStorageModePrivate);
```

```cpp
MTL::VertexDescriptor* vertexDescriptor = MTL::VertexDescriptor::alloc()->init();
vertexDescriptor->attributes()->object(0)->setFormat(MTL::VertexFormatFloat3);
vertexDescriptor->attributes()->object(0)->setOffset(0);
vertexDescriptor->attributes()->object(0)->setBufferIndex(0);
vertexDescriptor->layouts()->object(0)->setStride(12);
vertexDescriptor->layouts()->object(0)->setStepFunction(MTL::VertexStepFunctionPerPatchControlPoint);

MTL::RenderPipelineDescriptor* descriptor = MTL::RenderPipelineDescriptor::alloc()->init();
descriptor->setVertexDescriptor(vertexDescriptor);
descriptor->setVertexFunction(library->newFunction(MTLSTR("vertex_terrain")));
descriptor->setFragmentFunction(library->newFunction(MTLSTR("fragment_terrain")));
descriptor->colorAttachments()->object(0)->setPixelFormat(MTL::PixelFormatBGRA8Unorm);
descriptor->setDepthAttachmentPixelFormat(MTL::PixelFormatDepth32Float);

descriptor->setTessellationFactorFormat(MTL::TessellationFactorFormatHalf);
descriptor->setTessellationFactorStepFunction(MTL::TessellationFactorStepFunctionPerPatch);
descriptor->setTessellationPartitionMode(MTL::TessellationPartitionModeFractionalEven);
descriptor->setTessellationOutputWindingOrder(MTL::WindingCounterClockwise);
descriptor->setMaxTessellationFactor(16);
```

```cpp
// 1. Compute pass: fill the factor buffer.
MTL::ComputeCommandEncoder* compute = commandBuffer->computeCommandEncoder();
compute->setComputePipelineState(factorPipeline);
compute->setBuffer(factorBuffer, 0, 0);
compute->setBytes(&level, sizeof(float), 1);
compute->dispatchThreads(MTL::Size::Make(patchCount, 1, 1),
                         MTL::Size::Make(factorPipeline->threadExecutionWidth(), 1, 1));
compute->endEncoding();

// 2. Render pass: draw the patches.
encoder->setRenderPipelineState(terrainPipeline);
encoder->setVertexBuffer(controlPointBuffer, 0, 0);
encoder->setTessellationFactorBuffer(factorBuffer, 0, 0);      // buffer, offset, instance stride
encoder->setVertexTexture(heightMap, 0);
encoder->setVertexSamplerState(samplerState, 0);
encoder->setTriangleFillMode(MTL::TriangleFillModeLines);      // to see the subdivision
encoder->drawPatches(4,                // control points per patch
                     0,                // patch start
                     patchCount,
                     nullptr,          // patch index buffer
                     0,                // patch index buffer offset
                     1,                // instance count
                     0);               // base instance
```
