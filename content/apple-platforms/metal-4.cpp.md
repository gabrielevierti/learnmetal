```cpp
MTL4::CommandQueue* commandQueue = device->newMTL4CommandQueue();
MTL4::CommandBuffer* commandBuffer = device->newCommandBuffer();
MTL4::CommandAllocator* allocators[3];                  // one per frame in flight
for (auto& allocator : allocators) {
    allocator = device->newCommandAllocator();
}
```

```cpp
MTL4::CommandAllocator* allocator = allocators[frameNumber % 3];
allocator->reset();                                     // the GPU finished with this memory three frames ago
commandBuffer->beginCommandBuffer(allocator);

MTL4::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(passDescriptor);
// ... encode draws ...
encoder->endEncoding();

commandBuffer->endCommandBuffer();
commandQueue->waitForDrawable(drawable);
commandQueue->commit(&commandBuffer, 1);
commandQueue->signalDrawable(drawable);
drawable->present();
```

```cpp
MTL4::ArgumentTableDescriptor* tableDescriptor = MTL4::ArgumentTableDescriptor::alloc()->init();
tableDescriptor->setMaxBufferBindCount(2);
tableDescriptor->setMaxTextureBindCount(1);
tableDescriptor->setMaxSamplerStateBindCount(1);
NS::Error* error = nullptr;
MTL4::ArgumentTable* arguments = device->newArgumentTable(tableDescriptor, &error);

arguments->setAddress(vertexBuffer->gpuAddress(), 0);                   // [[buffer(0)]]
arguments->setAddress(uniformBuffer->gpuAddress() + offset, 1);
arguments->setTexture(colorTexture->gpuResourceID(), 0);                // [[texture(0)]]
arguments->setSamplerState(sampler->gpuResourceID(), 0);
```

```cpp
encoder->setRenderPipelineState(pipelineState);
encoder->setArgumentTable(arguments, MTL::RenderStageVertex | MTL::RenderStageFragment);
encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(3));
```

```cpp
MTL::ResidencySetDescriptor* residencyDescriptor = MTL::ResidencySetDescriptor::alloc()->init();
residencyDescriptor->setInitialCapacity(64);
MTL::ResidencySet* residencySet = device->newResidencySet(residencyDescriptor, &error);

residencySet->addAllocation(vertexBuffer);
residencySet->addAllocation(uniformBuffer);
residencySet->addAllocation(colorTexture);
residencySet->commit();                                 // apply the additions

commandQueue->addResidencySet(residencySet);            // every command buffer on this queue can use them
commandQueue->addResidencySet(metalLayer->residencySet());   // the drawables' textures
```

```cpp
MTL4::CompilerDescriptor* compilerDescriptor = MTL4::CompilerDescriptor::alloc()->init();
MTL4::Compiler* compiler = device->newCompiler(compilerDescriptor, &error);

MTL4::LibraryFunctionDescriptor* vertexFunction = MTL4::LibraryFunctionDescriptor::alloc()->init();
vertexFunction->setLibrary(library);
vertexFunction->setName(MTLSTR("vertex_main"));
MTL4::LibraryFunctionDescriptor* fragmentFunction = MTL4::LibraryFunctionDescriptor::alloc()->init();
fragmentFunction->setLibrary(library);
fragmentFunction->setName(MTLSTR("fragment_main"));

MTL4::RenderPipelineDescriptor* descriptor = MTL4::RenderPipelineDescriptor::alloc()->init();
descriptor->setVertexFunctionDescriptor(vertexFunction);
descriptor->setFragmentFunctionDescriptor(fragmentFunction);
descriptor->colorAttachments()->object(0)->setPixelFormat(MTL::PixelFormatBGRA8Unorm);

MTL::RenderPipelineState* pipelineState = compiler->newRenderPipelineState(descriptor, nullptr, &error);
```
