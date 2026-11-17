```cpp
// Without MetalKit's loader: decode six files with stb_image and copy each into one slice.
const char* names[6] = {"right.jpg", "left.jpg", "top.jpg", "bottom.jpg", "front.jpg", "back.jpg"};
MTL::Texture* skybox = nullptr;
for (int face = 0; face < 6; face++) {
    int width, height, channels;
    unsigned char* pixels = stbi_load(names[face], &width, &height, &channels, 4);
    if (!skybox) {
        skybox = device->newTexture(MTL::TextureDescriptor::textureCubeDescriptor(
            MTL::PixelFormatRGBA8Unorm, width, false));
    }
    skybox->replaceRegion(MTL::Region::Make2D(0, 0, width, height), 0, face,
                          pixels, width * 4, width * height * 4);
    stbi_image_free(pixels);
}
```

```cpp
// One image with the six faces stacked top to bottom: each face is a block of rows.
int width, height, channels;
unsigned char* pixels = stbi_load("skybox_strip.png", &width, &height, &channels, 4);
int size = width;                                            // faces are square, height == 6 * width
MTL::Texture* skybox = device->newTexture(MTL::TextureDescriptor::textureCubeDescriptor(
    MTL::PixelFormatRGBA8Unorm, size, false));
for (int face = 0; face < 6; face++) {
    skybox->replaceRegion(MTL::Region::Make2D(0, 0, size, size), 0, face,
                          pixels + face * size * size * 4, size * 4, size * size * 4);
}
stbi_image_free(pixels);
```

```cpp
MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::textureCubeDescriptor(
    MTL::PixelFormatRGBA8Unorm, 1024, false);
MTL::Texture* cube = device->newTexture(descriptor);
for (int face = 0; face < 6; face++) {
    cube->replaceRegion(MTL::Region::Make2D(0, 0, 1024, 1024),
                        0,                       // mipmap level
                        face,                    // slice
                        facePixels[face],
                        1024 * 4,                // bytes per row
                        1024 * 1024 * 4);        // bytes per image
}
```

```cpp
MTL::DepthStencilDescriptor* skyDepth = MTL::DepthStencilDescriptor::alloc()->init();
skyDepth->setDepthCompareFunction(MTL::CompareFunctionLessEqual);
skyDepth->setDepthWriteEnabled(false);
```

```cpp
pass->colorAttachments()->object(0)->setTexture(environmentCube);
pass->colorAttachments()->object(0)->setSlice(face);
```

```cpp
inline simd::float4x4 lookAtLH(simd::float3 eye, simd::float3 center, simd::float3 up) {
    simd::float3 z = simd::normalize(center - eye);
    simd::float3 x = simd::normalize(simd::cross(up, z));
    simd::float3 y = simd::cross(z, x);
    return simd_matrix(simd_make_float4(x.x, y.x, z.x, 0),
                       simd_make_float4(x.y, y.y, z.y, 0),
                       simd_make_float4(x.z, y.z, z.z, 0),
                       simd_make_float4(-simd::dot(x, eye), -simd::dot(y, eye), -simd::dot(z, eye), 1));
}

inline simd::float4x4 perspectiveLH(float fovY, float aspect, float near, float far) {
    float y = 1.0f / std::tan(fovY * 0.5f);
    float x = y / aspect;
    float z = far / (far - near);
    return simd_matrix(simd_make_float4(x, 0, 0, 0),
                       simd_make_float4(0, y, 0, 0),
                       simd_make_float4(0, 0, z, 1),
                       simd_make_float4(0, 0, -near * z, 0));
}
```
