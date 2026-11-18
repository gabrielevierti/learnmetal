Create the scaler with the half-size input and the drawable-size output, encode it after the scene pass, and let the final pass sample the upscaled texture. Edges and texture detail are visibly crisper than with the linear filter, which only blurs. Thin lines still flicker, because a spatial scaler cannot invent samples it never had; that is what the temporal scaler fixes.
---
Return the motion from a debug pass, scaled up so it is visible.

```cpp
float2 motion = motionTexture.sample(s, in.uv).rg;
return float4(abs(motion) * 20.0, 0.0, 1.0);
```

With a still camera the image is black except for moving objects. Panning right tints everything red, tilting tints it green, and nearer surfaces are brighter than far ones, because they move farther on screen.
---
The scaler assumes the samples sit at pixel centers while they are in fact shifted every frame. It lines the history up wrongly, and the image shakes by a fraction of a pixel or turns soft. The opposite mistake, sending offsets without jittering the projection, gives a stable image with no extra detail and no anti-aliasing.
