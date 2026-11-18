Compute the grid position from the instance ID in the vertex function, with no instance buffer at all.

```cpp
float column = float(instanceID % 100);
float row = float(instanceID / 100);
float3 offset = float3(column - 50.0, 0.0, row - 50.0) * 1.5;
out.position = uniforms.projection * uniforms.view * float4(in.position + offset, 1.0);
out.color = float3(column, row, 50.0) / 100.0;
```

Draw with an instance count of 10,000.
---
Rotate the instance's world position around the y axis by an angle that depends on time. The instance buffer is never rewritten.

```cpp
float angle = uniforms.time * 0.05;
float c = cos(angle), s = sin(angle);
float4 world = instance.model * float4(in.position, 1.0);
world.xz = float2(world.x * c + world.z * s, world.z * c - world.x * s);
```

The live demo does this: the ring's angle includes `uniforms.time`.
