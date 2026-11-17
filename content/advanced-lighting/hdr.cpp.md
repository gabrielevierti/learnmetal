```cpp
MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
    MTL::PixelFormatRGBA16Float, width, height, false);
descriptor->setUsage(MTL::TextureUsageRenderTarget | MTL::TextureUsageShaderRead);
descriptor->setStorageMode(MTL::StorageModePrivate);
hdrColor = device->newTexture(descriptor);
```
