```cpp
// There is no view to do this for us. Create a 4x multisample color (and depth) texture
// the size of the drawable, render into it, and resolve into the drawable's texture.
const NS::UInteger sampleCount = 4;
```

```cpp
pipelineDescriptor->setRasterSampleCount(4);
```

```cpp
MTL::TextureDescriptor* msaaDescriptor = MTL::TextureDescriptor::texture2DDescriptor(
    MTL::PixelFormatBGRA8Unorm, width, height, false);
msaaDescriptor->setTextureType(MTL::TextureType2DMultisample);
msaaDescriptor->setSampleCount(4);
msaaDescriptor->setUsage(MTL::TextureUsageRenderTarget);
msaaDescriptor->setStorageMode(MTL::StorageModeMemoryless);     // StorageModePrivate on Intel Macs
MTL::Texture* msaaColor = device->newTexture(msaaDescriptor);
```

```cpp
pass->colorAttachments()->object(0)->setTexture(msaaColor);
pass->colorAttachments()->object(0)->setResolveTexture(sceneColor);       // ordinary texture, or the drawable's
pass->colorAttachments()->object(0)->setLoadAction(MTL::LoadActionClear);
pass->colorAttachments()->object(0)->setStoreAction(MTL::StoreActionMultisampleResolve);
pass->depthAttachment()->setTexture(msaaDepth);
pass->depthAttachment()->setStoreAction(MTL::StoreActionDontCare);
```
