Drawn first, the sky's fragment function runs for every pixel of the screen, and most of those pixels are then overdrawn by the scene. Drawn last with `.lessEqual`, it runs only where nothing else was drawn. On Apple GPUs hidden surface removal narrows the gap for opaque draws, but drawing the sky last is never slower.
---
Use the Fresnel effect: more reflection at grazing angles.

```cpp
float fresnel = pow(1.0 - max(dot(-incident, normal), 0.0), 5.0);
float3 color = mix(refracted, reflected, saturate(0.04 + 0.96 * fresnel));
```

In the live demo, replace the last line of the shader with this to get a glass ball with reflective edges.
