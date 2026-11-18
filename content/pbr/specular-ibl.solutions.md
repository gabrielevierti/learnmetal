Sample the prefiltered cubemap in the skybox shader at a fixed level.

```cpp
return float4(prefilterMap.sample(s, in.direction, level(uniforms.mip)).rgb, 1.0);
```

Level 0 is the sharp environment and each higher level is blurrier.
---
The irradiance map, the prefiltered map and the lookup table depend only on the environment, and the table not even on that. After generating them, read each mip level and face back with a blit into a buffer and write the bytes to a file; at the next launch fill the textures with `replace`. A common container for this is KTX.
---
Nothing about the material changes. Regenerate the irradiance and prefiltered maps for each environment and bind them. The same object looks blue-tinted under an open sky and warm in a sunset, which is the practical benefit of physically based materials.
