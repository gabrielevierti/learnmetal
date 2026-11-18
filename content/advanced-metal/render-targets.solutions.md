Create the offscreen textures at half the drawable size; the full-screen pass stretches them. With `.nearest` you see blocky doubled pixels, with `.linear` a soft blur. Rendering at reduced resolution and upscaling is a standard way to save GPU time, and MetalFX does the upscaling far better than a linear filter.
---
Add a second small color texture and render the scene into it with a view matrix that looks along `-camera.front`. Then, in the main pass, draw a small quad near the top of the screen that samples it. Mirror the image horizontally by flipping u, as a real mirror does.

```cpp
float2 uv = float2(1.0 - in.uv.x, in.uv.y);
return mirrorTexture.sample(s, uv);
```
