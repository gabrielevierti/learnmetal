Negate y when writing the position. Only the vertex function changes.

```cpp
out.position = float4(in.position.x, -in.position.y, in.position.z, 1.0);
```
---
Give the vertex function its own uniform struct at a free buffer index and add the offset. On the CPU set `offset = (cos(time), sin(time)) * 0.3` each frame and send it with `setVertexBytes` at index 1.

```cpp
struct VertexUniforms {
    float2 offset;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant VertexUniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    out.position = float4(in.position.xy + uniforms.offset, in.position.z, 1.0);
    out.color = float4(in.color, 1.0);
    return out;
}
```
---
The bottom-left vertex is at (-0.5, -0.5, 0). Used as a color that is negative red and green and zero blue, and the color attachment clamps negative values to 0, so that corner is black. The interpolated values only become positive, and visible, toward the right and top of the triangle.
