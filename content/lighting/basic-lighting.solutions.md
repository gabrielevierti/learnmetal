Compute the position from the time each frame and use it both for the uniform and for the lamp's model matrix: `(cos(time) * 2, 1, sin(time) * 2)`. The live demo above does exactly this.
---
At 2 the highlight covers most of the face and looks like extra diffuse light. At 8 it is a wide soft glow, at 64 a small spot, and at 256 a tiny pinpoint, like polished metal or wet plastic. The exponent only narrows the lobe; it does not change its peak brightness.
---
The vertex function computes one color per vertex and the rasterizer interpolates it linearly. A highlight that falls in the middle of a face is missed entirely, because no vertex sees it, and one near a corner is smeared across the triangle. On a cube with 2 triangles per face the effect is extreme. Per-fragment lighting evaluates the formula at every pixel, so the highlight keeps its shape.
