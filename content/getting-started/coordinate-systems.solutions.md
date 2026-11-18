A larger field of view fits more of the scene into the view, so objects look smaller and perspective gets stronger near the edges; a small one acts like a telephoto lens. An aspect ratio that does not match the view stretches the image: too large squeezes everything horizontally, too small widens it. That is why the aspect ratio must be recomputed when the view is resized.
---
Add the time to the angle of every third cube when building its model matrix: in Swift, `var angle = (20 * Float(i)).radians; if i % 3 == 0 { angle += time }`. Nothing else changes, because each cube already gets its own matrix.
---
With `.always` every fragment passes, so the result depends on draw order: later cubes cover earlier ones even when they are farther away. With `.greater` a fragment passes only if it is farther than what is stored. The depth buffer is cleared to 1, the farthest value, so nothing passes and the view stays empty, unless you also clear the depth to 0.
