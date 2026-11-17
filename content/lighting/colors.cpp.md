```cpp
struct FragmentUniforms {
    simd::float3 objectColor;
    simd::float3 lightColor;
};

FragmentUniforms fragmentUniforms{ {1.0f, 0.5f, 0.31f}, {1, 1, 1} };
encoder->setFragmentBytes(&fragmentUniforms, sizeof(FragmentUniforms), 1);
```

```cpp
pipelineDescriptor->setFragmentFunction(library->newFunction(MTLSTR("fragment_light")));
lightPipelineState = device->newRenderPipelineState(pipelineDescriptor, &error);
```

```cpp
const simd::float3 lightPosition = {1.2f, 1.0f, 2.0f};

// The object
encoder->setRenderPipelineState(pipelineState);
uniforms.model = matrix_identity_float4x4;
encoder->setVertexBytes(&uniforms, sizeof(Uniforms), 1);
encoder->setFragmentBytes(&fragmentUniforms, sizeof(FragmentUniforms), 1);
encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(36));

// The lamp
encoder->setRenderPipelineState(lightPipelineState);
uniforms.model = translation(lightPosition) * scaling(simd::float3{0.2f, 0.2f, 0.2f});
encoder->setVertexBytes(&uniforms, sizeof(Uniforms), 1);
encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(36));
```
