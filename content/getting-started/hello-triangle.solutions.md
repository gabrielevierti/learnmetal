Append three more vertices to the array, for example the first triangle shifted by 0.6 on x and scaled down, and draw with a vertex count of 6. The buffer length follows the array automatically.

```cpp
// x      y     z
-0.9, -0.4, 0.0,    -0.1, -0.4, 0.0,    -0.5, 0.4, 0.0,     // first triangle
 0.1, -0.4, 0.0,     0.9, -0.4, 0.0,     0.5, 0.4, 0.0,     // second triangle
```
---
Add a second fragment function, change only `fragmentFunction` on the descriptor, and create a second pipeline state from it. Then draw each triangle after setting its pipeline: vertex start 0, count 3 with the first state; vertex start 3, count 3 with the second.

```cpp
fragment float4 fragment_yellow(VertexOut in [[stage_in]]) {
    return float4(1.0, 1.0, 0.0, 1.0);
}
```
---
Set a vertex to x = 1.5. The triangle is cut by the edge of the view: the GPU clips it against the -1 to 1 volume and rasterizes only the part inside. Nothing wraps around and nothing crashes. Clipping on z works the same way, which is why geometry in front of the near plane disappears.
