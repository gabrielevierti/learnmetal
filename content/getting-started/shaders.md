# Shaders

Shaders are where graphics programming happens. This chapter looks at the Metal Shading Language more closely, and shows the two ways data reaches a shader: per-vertex attributes that are interpolated across a triangle, and uniforms that are the same for a whole draw call.

## The language in brief

MSL is based on C++14. The types you will use all the time:

| Type | Meaning |
| --- | --- |
| `float`, `int`, `uint`, `bool` | Scalars. `half` is a 16-bit float, often faster on mobile GPUs. |
| `float2`, `float3`, `float4` | Vectors. Also `int2`, `uint3`, `half4`, and so on. |
| `float3x3`, `float4x4` | Matrices, stored column by column. |
| `texture2d<float>`, `texturecube<float>`, `depth2d<float>` | Textures. |
| `sampler` | Filtering and addressing settings for reading a texture. |

Vectors support **swizzling**: `v.xyz`, `v.rg`, `v.zyx`, `color.rgb * color.a`. The standard library has the functions you expect: `dot`, `cross`, `normalize`, `length`, `reflect`, `mix`, `clamp`, `saturate`, `pow`, `smoothstep`, `max`, `min`.

Things MSL does not allow: recursion, lambdas, virtual functions, exceptions, `new`, and the C++ standard library.

## Passing data between stages

Whatever the vertex function returns is interpolated across the triangle and handed to the fragment function. Add a color to the output struct:

```cpp
struct VertexOut {
    float4 position [[position]];
    float4 color;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]]) {
    VertexOut out;
    out.position = float4(in.position, 1.0);
    out.color = float4(in.position.x + 0.5, in.position.y + 0.5, 0.5, 1.0);
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]]) {
    return in.color;
}
```

Each vertex computes a color from its own position, and every fragment in between receives a blend of the three. This interpolation is automatic for every member of the struct.

## More vertex attributes

Colors can also come from the vertex buffer. Interleave them with the positions:

```swift
let vertices: [Float] = [
    // position         // color
    -0.5, -0.5, 0.0,    1.0, 0.0, 0.0,
     0.5, -0.5, 0.0,    0.0, 1.0, 0.0,
     0.0,  0.5, 0.0,    0.0, 0.0, 1.0,
]
```

Describe the second attribute and the larger stride:

```swift
let floatSize = MemoryLayout<Float>.stride
vertexDescriptor.attributes[0].format = .float3
vertexDescriptor.attributes[0].offset = 0
vertexDescriptor.attributes[0].bufferIndex = 0
vertexDescriptor.attributes[1].format = .float3
vertexDescriptor.attributes[1].offset = floatSize * 3
vertexDescriptor.attributes[1].bufferIndex = 0
vertexDescriptor.layouts[0].stride = floatSize * 6
```

And receive it in the shader:

```cpp
struct VertexIn {
    float3 position [[attribute(0)]];
    float3 color    [[attribute(1)]];
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]]) {
    VertexOut out;
    out.position = float4(in.position, 1.0);
    out.color = float4(in.color, 1.0);
    return out;
}
```

The result is the classic triangle with a red, a green and a blue corner blending into each other.

## Uniforms

A **uniform** is data that stays constant during a draw call: a time value, a transformation matrix, a light position. In Metal a uniform is simply a struct in a buffer that the shader receives by reference.

Declare the struct in the shader and add it as a parameter:

```cpp
struct Uniforms {
    float time;
    float4 tint;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant Uniforms &uniforms [[buffer(0)]]) {
    float pulse = sin(uniforms.time) * 0.5 + 0.5;
    return in.color * uniforms.tint * pulse;
}
```

`constant` is the address space for read-only buffer data. `[[buffer(0)]]` is slot 0 of the **fragment** buffer table. Vertex and fragment functions have separate tables, so vertex buffer 0 and fragment buffer 0 are unrelated.

Declare a matching struct in Swift:

```swift
struct Uniforms {
    var time: Float
    var tint: SIMD4<Float>
}
```

For small data, the simplest way to send it is `setFragmentBytes`, which copies the bytes into a temporary buffer managed by Metal:

```swift
var uniforms = Uniforms(time: Float(CACurrentMediaTime() - startTime),
                        tint: [1, 1, 1, 1])
encoder.setFragmentBytes(&uniforms,
                         length: MemoryLayout<Uniforms>.stride,
                         index: 0)
```

Store `startTime = CACurrentMediaTime()` in `init`; a `Float` cannot hold the raw value precisely enough. There is a matching `setVertexBytes` for the vertex stage. For data larger than 4 KB, or data shared by many draws, create an `MTLBuffer` yourself and bind it with `setFragmentBuffer`.

## Keeping Swift and MSL layouts in sync

The Swift struct and the MSL struct must have identical memory layouts. Nothing checks this for you, and a mismatch produces garbage values, not an error. Three rules prevent nearly all problems:

1. Use `SIMD` types in Swift for vectors and `simd_float4x4` (`float4x4`) for matrices. `SIMD4<Float>` matches `float4`, `SIMD2<Float>` matches `float2`.
2. `SIMD3<Float>` and MSL `float3` both occupy **16 bytes**, not 12. They match each other, but they do not match three loose floats. When you need a tightly packed 12-byte vector in a buffer, MSL has `packed_float3`.
3. Always use `MemoryLayout<T>.stride`, not `.size`, for buffer lengths.

In our struct, `time` is 4 bytes followed by 12 bytes of padding so that `tint` starts at offset 16, in both languages.

!!! note "One definition for both languages"
    Larger projects put shared structs in a C header that is included by the `.metal` file and exposed to Swift through a bridging header. Then there is only one definition and the layouts cannot drift. This series repeats the structs on both sides to keep each chapter readable on its own.

## Exercises

- Flip the triangle upside down in the vertex function only.
- Add a `float2 offset` uniform for the vertex stage and move the triangle in a circle over time.
- Output the position as the color (`out.color = out.position`). Why is the bottom-left corner black?
