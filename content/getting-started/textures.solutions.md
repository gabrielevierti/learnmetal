Sample with `in.uv * 2.0`. With `.repeat` you see four copies, with `.mirrorRepeat` the copies are mirrored so the seams match, and with `.clampToEdge` the image fills one quarter and its edge pixels stretch across the rest. You can try all three in the live demo above by raising the UV scale.
---
Set `minFilter` and `magFilter` to `.nearest` and remap the coordinates so the quad shows a tenth of the image. Each texel becomes a visible square. Switch back to `.linear` and the squares blend into a blur.

```cpp
float2 uv = 0.45 + in.uv * 0.1;
return colorTexture.sample(textureSampler, uv);
```
---
Add a float to a uniform struct for the fragment stage, bind it with `setFragmentBytes`, and set it to `sin(time) * 0.5 + 0.5` each frame.

```cpp
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant float &mixFactor [[buffer(0)]],
                              texture2d<float> texture0 [[texture(0)]],
                              texture2d<float> texture1 [[texture(1)]],
                              sampler textureSampler [[sampler(0)]]) {
    return mix(texture0.sample(textureSampler, in.uv),
               texture1.sample(textureSampler, in.uv), mixFactor);
}
```
