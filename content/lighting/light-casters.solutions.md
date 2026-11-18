Use a direction close to horizontal, such as (-1.0, -0.15, -0.3), and a diffuse color like (1.0, 0.55, 0.25) with a dim bluish ambient such as (0.05, 0.06, 0.1). Long shading gradients and warm highlights do the rest.
---
Start from the table: for a range of about 13 units use linear 0.35 and quadratic 0.44. Raise the quadratic term to make the light die sooner without darkening what is close; raise the linear term to darken everything more evenly.
---
Build a view-projection matrix for the spotlight, as for a camera at the light looking along its direction. Transform the fragment's world position with it, divide by w, and map from -1...1 to 0...1 to get a texture coordinate. Multiply the light's color by the sampled image.

```cpp
float4 lightClip = uniforms.lightViewProjection * float4(in.worldPosition, 1.0);
float2 slideUV = lightClip.xy / lightClip.w * float2(0.5, -0.5) + 0.5;
float3 slide = slideTexture.sample(clampSampler, slideUV).rgb;
diffuse *= slide * intensity;
```

This is the first half of shadow mapping: the same projection later looks up a depth instead of a color.
