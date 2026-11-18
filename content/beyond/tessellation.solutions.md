Pass `level = 1.0 + 7.5 * (sin(time) * 0.5 + 0.5)` to the factor kernel each frame. With a fractional partition mode the new vertices slide out of existing edges smoothly. The live demo has a slider for the factor.
---
Give the kernel the control points and the camera position. For each edge take its midpoint, compute the distance to the camera, and map it to a factor. Use the average of the edge factors for the inside.

```cpp
static float edgeFactor(float3 a, float3 b, float3 eye) {
    float distance = length((a + b) * 0.5 - eye);
    return clamp(48.0 / distance, 1.0, 16.0);
}
```

Because the factor depends only on the edge's own endpoints, both patches that share an edge compute the same value and no cracks appear.
---
With `.integer` the factor snaps to whole numbers, so the mesh changes in visible jumps as you move. With `.fractionalEven` new vertices grow out of existing ones, and the transition is continuous. Fractional modes cost nothing extra and are the right default for anything that moves.
