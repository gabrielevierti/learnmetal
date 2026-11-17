```cpp
// stb_image decodes Radiance .hdr files to floats with stbi_loadf.
MTL::Texture* loadHDRTexture(MTL::Device* device, const char* path) {
    int width, height, channels;
    float* pixels = stbi_loadf(path, &width, &height, &channels, 4);      // RGBA, 32-bit float
    if (!pixels) return nullptr;

    MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
        MTL::PixelFormatRGBA32Float, width, height, false);
    MTL::Texture* texture = device->newTexture(descriptor);
    texture->replaceRegion(MTL::Region::Make2D(0, 0, width, height), 0,
                           pixels, width * 4 * sizeof(float));
    stbi_image_free(pixels);
    return texture;
}
```

```cpp
#include <functional>

void renderToCube(MTL::Texture* cube, NS::UInteger level, MTL::CommandBuffer* commandBuffer,
                  const std::function<void(MTL::RenderCommandEncoder*, simd::float4x4)>& draw) {
    simd::float4x4 projection = perspectiveLH(float(M_PI) / 2, 1.0f, 0.1f, 10.0f);
    for (int face = 0; face < 6; face++) {
        MTL::RenderPassDescriptor* pass = MTL::RenderPassDescriptor::alloc()->init();
        pass->colorAttachments()->object(0)->setTexture(cube);
        pass->colorAttachments()->object(0)->setSlice(face);
        pass->colorAttachments()->object(0)->setLevel(level);
        pass->colorAttachments()->object(0)->setLoadAction(MTL::LoadActionDontCare);
        pass->colorAttachments()->object(0)->setStoreAction(MTL::StoreActionStore);

        MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(pass);
        simd::float4x4 view = lookAtLH(simd::float3{0, 0, 0}, faces[face].direction, faces[face].up);
        draw(encoder, projection * view);
        encoder->endEncoding();
        pass->release();
    }
}
```
