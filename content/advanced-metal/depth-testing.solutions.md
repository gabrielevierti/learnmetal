With `.always` nothing is ever rejected, so each pixel shows whatever was drawn last. Objects drawn later appear in front of objects drawn earlier even when they are behind them, and within one cube the faces at the end of the vertex buffer cover the others.
---
At close range the two quads have distinct depth values. As the camera moves away, both depths approach 1 and round to the same number, and the flickering stripes appear. Each remedy works: a larger gap, a farther near plane (try 1.0 instead of 0.1), a depth bias on the second quad with `setDepthBias`, or reverse-Z.
