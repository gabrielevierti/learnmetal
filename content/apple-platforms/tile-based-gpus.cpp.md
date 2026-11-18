```cpp
MTL::RenderPassDescriptor* pass = MTL::RenderPassDescriptor::alloc()->init();
auto* color = pass->colorAttachments()->object(0);
color->setTexture(drawable->texture());
color->setLoadAction(MTL::LoadActionClear);             // every pixel gets drawn: nothing to load
color->setStoreAction(MTL::StoreActionStore);           // the image is what we want
auto* depth = pass->depthAttachment();
depth->setTexture(depthTexture);
depth->setLoadAction(MTL::LoadActionClear);
depth->setStoreAction(MTL::StoreActionDontCare);        // nobody reads the depth after this pass
```

```cpp
MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
    MTL::PixelFormatDepth32Float, width, height, false);
descriptor->setUsage(MTL::TextureUsageRenderTarget);
descriptor->setStorageMode(MTL::StorageModeMemoryless); // exists only in tile memory
MTL::Texture* depthTexture = device->newTexture(descriptor);
```
