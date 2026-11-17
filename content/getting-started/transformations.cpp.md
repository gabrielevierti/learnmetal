```cpp
simd::float4x4 transform = translation * rotation * scale;
// applied to a vertex: scale first, then rotate, then translate
```

```cpp
// Math.hpp
#pragma once
#include <simd/simd.h>
#include <cmath>

inline float radians(float degrees) { return degrees * float(M_PI) / 180.0f; }

inline simd::float4x4 translation(simd::float3 t) {
    simd::float4x4 m = matrix_identity_float4x4;
    m.columns[3] = simd_make_float4(t, 1.0f);
    return m;
}

inline simd::float4x4 scaling(simd::float3 s) {
    return simd_diagonal_matrix(simd_make_float4(s, 1.0f));
}

inline simd::float4x4 rotation(float angle, simd::float3 axis) {
    return simd_matrix4x4(simd_quaternion(angle, simd::normalize(axis)));
}

/// The upper-left 3x3 part: rotation and scale without translation.
inline simd::float3x3 upperLeft(const simd::float4x4& m) {
    return simd_matrix(m.columns[0].xyz, m.columns[1].xyz, m.columns[2].xyz);
}
```

```cpp
struct Uniforms {
    simd::float4x4 transform;
};

// in draw()
float time = float(glfwGetTime());
Uniforms uniforms{
    translation(simd::float3{0.5f, -0.5f, 0.0f})
        * rotation(time, simd::float3{0, 0, 1})
        * scaling(simd::float3{0.5f, 0.5f, 0.5f})
};
encoder->setVertexBytes(&uniforms, sizeof(Uniforms), 1);
```
