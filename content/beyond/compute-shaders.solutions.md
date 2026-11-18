```cpp
kernel void invert(texture2d<float, access::read>  input  [[texture(0)]],
                   texture2d<float, access::write> output [[texture(1)]],
                   uint2 gid [[thread_position_in_grid]]) {
    float4 color = input.read(gid);
    output.write(float4(1.0 - color.rgb, color.a), gid);
}
```

Create the output texture with `.shaderWrite` and `.shaderRead` usage, then show it with the full-screen triangle.
---
```cpp
kernel void box_blur(texture2d<float, access::read>  input  [[texture(0)]],
                     texture2d<float, access::write> output [[texture(1)]],
                     uint2 gid [[thread_position_in_grid]]) {
    int2 size = int2(input.get_width(), input.get_height());
    float sum = 0.0;
    for (int x = -2; x < 2; x++) {
        for (int y = -2; y < 2; y++) {
            int2 p = clamp(int2(gid) + int2(x, y), int2(0), size - 1);
            sum += input.read(uint2(p)).r;
        }
    }
    output.write(float4(sum / 16.0), gid);
}
```

Input and output must be different textures.
---
Add a `float3 attractor` to the simulation uniforms and accelerate each particle toward it. Unproject the mouse position onto a plane in front of the camera to get the point.

```cpp
float3 toAttractor = uniforms.attractor - p.position;
float distanceSquared = max(dot(toAttractor, toAttractor), 0.25);
p.velocity += normalize(toAttractor) * (6.0 / distanceSquared) * uniforms.deltaTime;
```

The `max` keeps the force finite when a particle passes through the attractor.
