```cpp
std::mt19937 rng(7);
auto random = [&](float lo, float hi) { return std::uniform_real_distribution<float>(lo, hi)(rng); };

std::vector<simd::float4> kernel;
for (int i = 0; i < 64; i++) {
    simd::float3 sample = {random(-1, 1), random(-1, 1), random(0, 1)};
    sample = simd::normalize(sample) * random(0, 1);

    float t = float(i) / 64.0f;
    float scale = 0.1f + 0.9f * t * t;        // cluster near the center
    kernel.push_back(simd_make_float4(sample * scale, 0));
}
```

```cpp
std::vector<simd::float4> noise;
for (int i = 0; i < 16; i++) {
    noise.push_back(simd::float4{random(-1, 1), random(-1, 1), 0, 0});
}

MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
    MTL::PixelFormatRGBA32Float, 4, 4, false);
noiseTexture = device->newTexture(descriptor);
noiseTexture->replaceRegion(MTL::Region::Make2D(0, 0, 4, 4), 0,
                            noise.data(), 4 * sizeof(simd::float4));
```
