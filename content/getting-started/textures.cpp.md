```cpp
const float vertices[] = {
    // position            // uv
     0.5f,  0.5f, 0.0f,    1.0f, 0.0f,   // top right
     0.5f, -0.5f, 0.0f,    1.0f, 1.0f,   // bottom right
    -0.5f, -0.5f, 0.0f,    0.0f, 1.0f,   // bottom left
    -0.5f,  0.5f, 0.0f,    0.0f, 0.0f,   // top left
};
```

```cpp
const size_t floatSize = sizeof(float);
vertexDescriptor->attributes()->object(0)->setFormat(MTL::VertexFormatFloat3);
vertexDescriptor->attributes()->object(0)->setOffset(0);
vertexDescriptor->attributes()->object(0)->setBufferIndex(0);
vertexDescriptor->attributes()->object(1)->setFormat(MTL::VertexFormatFloat2);
vertexDescriptor->attributes()->object(1)->setOffset(floatSize * 3);
vertexDescriptor->attributes()->object(1)->setBufferIndex(0);
vertexDescriptor->layouts()->object(0)->setStride(floatSize * 5);
```

```cpp
// metal-cpp has no MTKTextureLoader. Decode the image with stb_image and upload the pixels.
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

MTL::Texture* loadTexture(MTL::Device* device, MTL::CommandQueue* queue, const char* path) {
    int width, height, channels;
    unsigned char* pixels = stbi_load(path, &width, &height, &channels, 4);   // force RGBA
    if (!pixels) { std::cerr << "Could not load " << path << "\n"; std::exit(1); }

    MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
        MTL::PixelFormatRGBA8Unorm, width, height, true);                     // true: allocate mipmaps
    descriptor->setUsage(MTL::TextureUsageShaderRead | MTL::TextureUsageRenderTarget);
    MTL::Texture* texture = device->newTexture(descriptor);
    texture->replaceRegion(MTL::Region::Make2D(0, 0, width, height), 0, pixels, width * 4);
    stbi_image_free(pixels);

    // Fill the mipmap chain on the GPU.
    MTL::CommandBuffer* commandBuffer = queue->commandBuffer();
    MTL::BlitCommandEncoder* blit = commandBuffer->blitCommandEncoder();
    blit->generateMipmaps(texture);
    blit->endEncoding();
    commandBuffer->commit();
    return texture;
}

texture = loadTexture(device, commandQueue, "container.jpg");
```

```cpp
MTL::SamplerState* samplerState;      // member of Renderer

// in the constructor
MTL::SamplerDescriptor* samplerDescriptor = MTL::SamplerDescriptor::alloc()->init();
samplerDescriptor->setMinFilter(MTL::SamplerMinMagFilterLinear);
samplerDescriptor->setMagFilter(MTL::SamplerMinMagFilterLinear);
samplerDescriptor->setMipFilter(MTL::SamplerMipFilterLinear);
samplerDescriptor->setSAddressMode(MTL::SamplerAddressModeRepeat);
samplerDescriptor->setTAddressMode(MTL::SamplerAddressModeRepeat);
samplerState = device->newSamplerState(samplerDescriptor);
samplerDescriptor->release();
```

```cpp
encoder->setFragmentTexture(texture, 0);
encoder->setFragmentSamplerState(samplerState, 0);
```
