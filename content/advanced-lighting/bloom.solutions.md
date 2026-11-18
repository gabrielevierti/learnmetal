Each pair of passes widens the blur a little, since repeated Gaussian blurs add up. Two iterations give a tight glow around the lamps; twenty give a wide haze, at twenty times the cost. That cost is the reason for the mip chain approach.
---
Make the two blur textures half the size of the scene. The blur then costs a quarter as much and covers twice the screen distance per pass. Because the glow is smooth, the lower resolution is not visible after the final upsample.
---
Create a chain of textures, each half the size of the previous. Downsample the bright texture into each level with a small filter, then go back up: upsample level n, add it to level n - 1, and repeat to the top. The live demo above uses the texture's own mipmaps as the downsample chain and sums five levels in one pass.
