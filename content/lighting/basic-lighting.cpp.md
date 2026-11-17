```cpp
struct Uniforms {
    simd::float4x4 model;
    simd::float4x4 view;
    simd::float4x4 projection;
    simd::float3x3 normalMatrix;
};

uniforms.normalMatrix = simd::transpose(simd::inverse(upperLeft(uniforms.model)));
```

```cpp
struct FragmentUniforms {
    simd::float3 objectColor;
    simd::float3 lightColor;
    simd::float3 lightPosition;
    simd::float3 viewPosition;
};

fragmentUniforms.lightPosition = lightPosition;
fragmentUniforms.viewPosition = camera.position;
```
