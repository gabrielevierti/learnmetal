In the lighting pass return one of the textures directly, remapping it into the visible range: normals as `n * 0.5 + 0.5`, positions scaled down. The live demo has a selector for this.
---
With forward rendering every fragment of every object loops over all 200 lights, including fragments that are later hidden. Deferred shading runs the loop once per screen pixel. With light volumes, or the distance test in the demo's shader, most pixels evaluate only the few lights that reach them.
---
Pass the inverse of the view-projection matrix. Rebuild the clip-space position from the texture coordinate and the stored depth, transform it, and divide by w.

```cpp
float depth = depthTexture.sample(s, in.uv);
float4 clip = float4(in.uv.x * 2.0 - 1.0, 1.0 - in.uv.y * 2.0, depth, 1.0);
float4 world = uniforms.inverseViewProjection * clip;
float3 position = world.xyz / world.w;
```
