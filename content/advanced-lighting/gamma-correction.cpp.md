```cpp
layer->setPixelFormat(MTL::PixelFormatBGRA8Unorm_sRGB);
```

```cpp
// Give loadTexture() a flag that picks the pixel format:
//   sRGB ? MTL::PixelFormatRGBA8Unorm_sRGB : MTL::PixelFormatRGBA8Unorm
diffuseMap  = loadTexture(device, commandQueue, "diffuse.png",  /* sRGB */ true);
specularMap = loadTexture(device, commandQueue, "specular.png", /* sRGB */ false);
normalMap   = loadTexture(device, commandQueue, "normal.png",   /* sRGB */ false);
```

```cpp
simd::float3 linear(simd::float3 srgb) {
    return {std::pow(srgb.x, 2.2f), std::pow(srgb.y, 2.2f), std::pow(srgb.z, 2.2f)};
}
```
