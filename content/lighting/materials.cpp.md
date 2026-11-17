```cpp
struct Material {
    simd::float3 ambient;
    simd::float3 diffuse;
    simd::float3 specular;
    float shininess;
};

struct Light {
    simd::float3 position;
    simd::float3 ambient;
    simd::float3 diffuse;
    simd::float3 specular;
};

struct FragmentUniforms {
    Material material;
    Light light;
    simd::float3 viewPosition;
};
```

```cpp
FragmentUniforms fragmentUniforms{
    Material{ {1.0f, 0.5f, 0.31f},     // ambient
              {1.0f, 0.5f, 0.31f},     // diffuse
              {0.5f, 0.5f, 0.5f},      // specular
              32.0f },                 // shininess
    Light{ lightPosition,
           {0.2f, 0.2f, 0.2f},         // ambient
           {0.5f, 0.5f, 0.5f},         // diffuse
           {1.0f, 1.0f, 1.0f} },       // specular
    camera.position
};
```

```cpp
simd::float3 lightColor = simd::float3{std::sin(time * 2.0f), std::sin(time * 0.7f), std::sin(time * 1.3f)} * 0.5f + 0.5f;
fragmentUniforms.light.diffuse = lightColor * 0.5f;
fragmentUniforms.light.ambient = lightColor * 0.1f;
```
