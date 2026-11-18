Keep an `exposure` value in the renderer, multiply or divide it by a constant such as 1.1 while a key is held, and send it in the tone mapping pass's uniforms. Multiplying, not adding, makes each step feel equal, because brightness perception is logarithmic.
---
Choose by the horizontal texture coordinate.

```cpp
float3 mapped = in.uv.x < 0.5 ? hdr / (hdr + 1.0) : acesFilm(hdr * uniforms.exposure);
```
