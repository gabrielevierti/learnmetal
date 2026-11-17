```cpp
const float vertices[] = {
    // position            // color
    -0.5f, -0.5f, 0.0f,    1.0f, 0.0f, 0.0f,
     0.5f, -0.5f, 0.0f,    0.0f, 1.0f, 0.0f,
     0.0f,  0.5f, 0.0f,    0.0f, 0.0f, 1.0f,
};
```

```cpp
const size_t floatSize = sizeof(float);
vertexDescriptor->attributes()->object(0)->setFormat(MTL::VertexFormatFloat3);
vertexDescriptor->attributes()->object(0)->setOffset(0);
vertexDescriptor->attributes()->object(0)->setBufferIndex(0);
vertexDescriptor->attributes()->object(1)->setFormat(MTL::VertexFormatFloat3);
vertexDescriptor->attributes()->object(1)->setOffset(floatSize * 3);
vertexDescriptor->attributes()->object(1)->setBufferIndex(0);
vertexDescriptor->layouts()->object(0)->setStride(floatSize * 6);
```

```cpp
#include <simd/simd.h>

struct Uniforms {
    float time;
    simd::float4 tint;
};
```

```cpp
Uniforms uniforms{ float(glfwGetTime()), simd::float4{1, 1, 1, 1} };
encoder->setFragmentBytes(&uniforms, sizeof(Uniforms), 0);    // bytes, length, index
```
