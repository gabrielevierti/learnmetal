Add an integer uniform and branch on it when computing the texture coordinate. At a low angle the simple version swims and distorts, the steep version is stable but shows layered steps on slopes, and occlusion mapping removes the steps.
---
From the final texture coordinate and depth, march toward the light in tangent space. If the height map rises above the ray at any step, the point is in shadow.

```cpp
float3 lightDir = normalize(transpose(TBN) * (uniforms.lightPosition - in.worldPosition));
float2 stepUV = float2(lightDir.x, -lightDir.y) / lightDir.z * uniforms.heightScale / 16.0;
float rayDepth = mapDepth;
float lit = 1.0;
for (int i = 0; i < 16; i++) {
    uv += stepUV;
    rayDepth -= mapDepth / 16.0;
    if (depthMap.sample(s, uv, level(0.0)).r < rayDepth) { lit = 0.3; break; }
}
```
