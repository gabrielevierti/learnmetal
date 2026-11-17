```cpp
encoder->drawPrimitives(MTL::PrimitiveTypeTriangle,
                        NS::UInteger(0),          // vertex start
                        NS::UInteger(36),         // vertex count
                        NS::UInteger(1000));      // instance count

encoder->drawIndexedPrimitives(MTL::PrimitiveTypeTriangle,
                               submesh.indexCount,
                               MTL::IndexTypeUInt32,
                               submesh.indexBuffer,
                               0,                 // index buffer offset
                               1000);             // instance count
```

```cpp
struct InstanceData {
    simd::float4x4 model;
    simd::float4 color;
};

MTL::Buffer* instanceBuffer = device->newBuffer(sizeof(InstanceData) * instanceCount,
                                                MTL::ResourceStorageModeShared);

InstanceData* instances = static_cast<InstanceData*>(instanceBuffer->contents());
for (int i = 0; i < instanceCount; i++) {
    instances[i] = InstanceData{transforms[i], colors[i]};
}
```

```cpp
encoder->setVertexBuffer(instanceBuffer, 0, 2);
```

```cpp
#include <random>

std::vector<simd::float4x4> makeAsteroidTransforms(int count, float radius, float spread) {
    std::mt19937 rng(42);
    auto random = [&](float lo, float hi) { return std::uniform_real_distribution<float>(lo, hi)(rng); };

    std::vector<simd::float4x4> transforms;
    for (int i = 0; i < count; i++) {
        float angle = float(i) / float(count) * 2.0f * float(M_PI);
        simd::float3 position = {std::sin(angle) * radius + random(-spread, spread),
                                 random(-spread, spread) * 0.4f,
                                 std::cos(angle) * radius + random(-spread, spread)};
        float scale = random(0.05f, 0.25f);

        transforms.push_back(translation(position)
                           * rotation(random(0, 2.0f * float(M_PI)), simd::float3{0.4f, 0.6f, 0.8f})
                           * scaling(simd::float3{scale, scale, scale}));
    }
    return transforms;
}
```
