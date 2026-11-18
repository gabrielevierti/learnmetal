Return the occlusion as a gray color from the composite pass, once from the raw texture and once from the blurred one. The live demo has both: choose "Occlusion buffer" and toggle the blur.
---
A radius near 0.5 world units darkens corners without haloing open surfaces; larger radii look dirty. Sixteen samples with the blur look close to sixty-four without it, at a quarter of the cost. Rendering the occlusion at half resolution halves the cost again.
