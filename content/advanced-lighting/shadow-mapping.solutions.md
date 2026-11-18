Bind the shadow map to a post-processing pass and output its value. Declare it as a normal depth texture and sample it with an ordinary sampler, not a comparison one.

```cpp
float depth = shadowMap.sample(plainSampler, in.uv);
return float4(float3(depth), 1.0);
```

You should see the scene from the light's position in shades of gray. If it is all white or all black, the light's near and far planes do not enclose the scene.
---
At zero, lit surfaces are covered with dark stripes or dots: acne, from fragments that land just behind the depth stored in their texel. With a large bias the stripes go away but shadows detach from the base of the objects and thin objects stop casting shadows: peter panning. The live demo has a bias slider.
---
Compute the light's position from the time and rebuild its view matrix every frame; the shadow pass and the main pass must use the same matrix. Keep the orthographic box centered on the scene, not on the light.
