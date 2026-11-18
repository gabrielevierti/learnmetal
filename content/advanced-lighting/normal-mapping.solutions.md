Because the normal and tangent are transformed with the normal matrix, the TBN basis rotates with the quad, and the sampled normals end up in world space. With a fixed light, the bright side of each brick should stay on the side facing the light while the quad turns. If the shading rotates with the quad instead, the tangent is not being transformed.
---
Scale before normalizing. The live demo has this as a slider.

```cpp
float3 tangentNormal = normalMap.sample(s, in.uv).xyz * 2.0 - 1.0;
tangentNormal.xy *= uniforms.strength;      // 0 is flat, above 1 exaggerates
float3 N = normalize(TBN * tangentNormal);
```
