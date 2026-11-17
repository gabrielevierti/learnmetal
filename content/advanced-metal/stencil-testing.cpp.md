```cpp
// The depth texture you create gets the combined format...
depthTextureDescriptor->setPixelFormat(MTL::PixelFormatDepth32Float_Stencil8);

// ...and is attached to the pass as both depth and stencil.
passDescriptor->depthAttachment()->setTexture(depthStencilTexture);
passDescriptor->stencilAttachment()->setTexture(depthStencilTexture);
passDescriptor->stencilAttachment()->setLoadAction(MTL::LoadActionClear);
passDescriptor->stencilAttachment()->setClearStencil(0);

pipelineDescriptor->setDepthAttachmentPixelFormat(MTL::PixelFormatDepth32Float_Stencil8);
pipelineDescriptor->setStencilAttachmentPixelFormat(MTL::PixelFormatDepth32Float_Stencil8);
```

```cpp
MTL::StencilDescriptor* writeStencil = MTL::StencilDescriptor::alloc()->init();
writeStencil->setStencilCompareFunction(MTL::CompareFunctionAlways);
writeStencil->setDepthStencilPassOperation(MTL::StencilOperationReplace);

MTL::DepthStencilDescriptor* writeDescriptor = MTL::DepthStencilDescriptor::alloc()->init();
writeDescriptor->setDepthCompareFunction(MTL::CompareFunctionLess);
writeDescriptor->setDepthWriteEnabled(true);
writeDescriptor->setFrontFaceStencil(writeStencil);
writeDescriptor->setBackFaceStencil(writeStencil);
MTL::DepthStencilState* writeState = device->newDepthStencilState(writeDescriptor);
```

```cpp
MTL::StencilDescriptor* testStencil = MTL::StencilDescriptor::alloc()->init();
testStencil->setStencilCompareFunction(MTL::CompareFunctionNotEqual);
testStencil->setDepthStencilPassOperation(MTL::StencilOperationKeep);

MTL::DepthStencilDescriptor* outlineDescriptor = MTL::DepthStencilDescriptor::alloc()->init();
outlineDescriptor->setDepthCompareFunction(MTL::CompareFunctionAlways);
outlineDescriptor->setDepthWriteEnabled(false);
outlineDescriptor->setFrontFaceStencil(testStencil);
outlineDescriptor->setBackFaceStencil(testStencil);
MTL::DepthStencilState* outlineState = device->newDepthStencilState(outlineDescriptor);
```

```cpp
// Floor and anything else that should not be outlined: the ordinary depth state.
encoder->setDepthStencilState(depthState);
drawFloor(encoder);

// 1. The cubes, marking the stencil buffer.
encoder->setDepthStencilState(writeState);
encoder->setStencilReferenceValue(1);
encoder->setRenderPipelineState(pipelineState);
drawCubes(encoder, 1.0f);

// 2. The outlines.
encoder->setDepthStencilState(outlineState);
encoder->setRenderPipelineState(solidColorPipelineState);
drawCubes(encoder, 1.05f);
```
