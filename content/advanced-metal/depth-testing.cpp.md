```cpp
MTL::DepthStencilDescriptor* descriptor = MTL::DepthStencilDescriptor::alloc()->init();
descriptor->setDepthCompareFunction(MTL::CompareFunctionLess);
descriptor->setDepthWriteEnabled(true);
MTL::DepthStencilState* depthState = device->newDepthStencilState(descriptor);
descriptor->release();
```

```cpp
passDescriptor->depthAttachment()->setClearDepth(0.0);
descriptor->setDepthCompareFunction(MTL::CompareFunctionGreater);
// and swap near and far when building the projection matrix
```
