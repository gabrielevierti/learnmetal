With `discard_fragment` the edges are hard: a pixel is in or out, and you see stair steps where the texture's alpha is partial. With blending the edges are smooth, but without sorting a nearer quad drawn first writes depth and cuts rectangular holes into the grass behind it. Cut-outs want discard (or alpha-to-coverage); real transparency wants blending with sorting.
---
The nearest window is drawn first and writes its depth. Every window behind it then fails the depth test, so it is missing where the near one covers it, even though you should see it through the glass. In the live demo, untick "sort back to front" and tick "windows write depth".
---
Enable blending with source factor `.one` (or `.sourceAlpha`) and destination factor `.one`, and turn depth writes off. Colors add up, so overlapping quads get brighter, and the order no longer matters, since addition is commutative. That is why additive particles need no sorting.
