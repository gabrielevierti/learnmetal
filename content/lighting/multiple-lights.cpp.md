```cpp
// C++ has real fixed-size arrays, so the layout matches the shader directly.
struct FragmentUniforms {
    DirectionalLight directionalLight;
    PointLight pointLights[4];
    SpotLight spotLight;
    simd::float3 viewPosition;
    float shininess;
};
```

```cpp
// pointLights is a std::vector<PointLight>
MTL::Buffer* lightBuffer = device->newBuffer(pointLights.data(),
                                             sizeof(PointLight) * pointLights.size(),
                                             MTL::ResourceStorageModeShared);
encoder->setFragmentBuffer(lightBuffer, 0, 2);      // buffer, offset, index
```

```cpp
const simd::float3 pointLightPositions[] = {
    { 0.7f,  0.2f,   2.0f},
    { 2.3f, -3.3f,  -4.0f},
    {-4.0f,  2.0f, -12.0f},
    { 0.0f,  0.0f,  -3.0f},
};
```
