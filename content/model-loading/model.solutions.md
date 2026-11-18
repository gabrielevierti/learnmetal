Call the model's draw method in a loop with a different model matrix each time, multiplying the per-instance translation and rotation by the normalization matrix. The vertex and index buffers are shared, so ten copies cost ten sets of draw calls and no extra memory. For many copies, switch to instancing.
---
Keep a dictionary from the texture's file path to the loaded texture, and look it up before loading. In Swift a `[URL: MTLTexture]` on the loader object; in C++ a `std::unordered_map<std::string, MTL::Texture*>`. Models commonly reference the same image from many materials, so this cuts both load time and memory.
---
Add `float3 baseColor` to the fragment uniforms, set it per submesh from the material, bind the 1 × 1 white texture where there is no image, and multiply.

```cpp
float3 albedo = baseColorTexture.sample(mapSampler, in.uv).rgb * uniforms.baseColor;
```

White times the color gives the color; an image times a white base color gives the image.
