Return the sampled value as a gray color from the main fragment function. Surfaces close to the light are dark and far ones bright, and each object is surrounded by a darker halo of the same shape on the walls behind it, which is its shadow before the comparison.
---
Set `renderTargetArrayLength = 6` on the pass, set `inputPrimitiveTopology = .triangle` on the pipeline, and draw every object with an instance count of 6. In the vertex function use `instanceID % 6` as the face: pick that face's matrix and write the face index to an output marked `[[render_target_array_index]]`.
