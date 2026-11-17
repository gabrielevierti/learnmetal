```cpp
MTL::Function* function = library->newFunction(MTLSTR("grayscale"));
NS::Error* error = nullptr;
MTL::ComputePipelineState* computePipeline = device->newComputePipelineState(function, &error);
```

```cpp
MTL::ComputeCommandEncoder* encoder = commandBuffer->computeCommandEncoder();
encoder->setComputePipelineState(computePipeline);
encoder->setTexture(inputTexture, 0);
encoder->setTexture(outputTexture, 1);

NS::UInteger width = computePipeline->threadExecutionWidth();
NS::UInteger height = computePipeline->maxTotalThreadsPerThreadgroup() / width;
encoder->dispatchThreads(MTL::Size::Make(inputTexture->width(), inputTexture->height(), 1),
                         MTL::Size::Make(width, height, 1));
encoder->endEncoding();
```

```cpp
encoder->setBuffer(particleBuffer, 0, 0);
encoder->setBytes(&simulationUniforms, sizeof(SimulationUniforms), 1);
encoder->dispatchThreads(MTL::Size::Make(particleCount, 1, 1),
                         MTL::Size::Make(computePipeline->threadExecutionWidth(), 1, 1));
```

```cpp
// Metal Performance Shaders has no metal-cpp wrapper. Call it from a small Objective-C++ file,
// like the window bridge in Project Setup:
//
//   MPSImageGaussianBlur* blur = [[MPSImageGaussianBlur alloc] initWithDevice:device sigma:8];
//   [blur encodeToCommandBuffer:commandBuffer sourceTexture:source destinationTexture:destination];
//
// metal-cpp objects are the Objective-C objects: cast with (__bridge id<MTLTexture>)texture.
```
