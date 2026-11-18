Subtract the sampled value from one.

```cpp
float3 specularColor = 1.0 - specularMap.sample(mapSampler, in.uv).rgb;
```
---
Nothing in the shader changes: the specular term is already multiplied by the map's rgb. A map painted blue over the steel gives blue highlights there. This is how colored metals are done in the Phong model.
---
Bind a third texture and add its color after the lighting, without multiplying by any light term.

```cpp
float3 emission = emissionMap.sample(mapSampler, in.uv).rgb;
return float4(ambient + diffuse + specular + emission, 1.0);
```

To keep the steel frame from glowing, multiply the emission by `1.0 - step(0.01, specularColor.r)` so it only shows where the specular map is black.
