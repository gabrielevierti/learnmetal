# Tessellation

Detailed surfaces need many triangles, but only where the viewer can see the detail. A mountain a kilometer away does not need the triangle density of the ground under your feet. **Tessellation** lets the GPU subdivide coarse geometry on the fly, as finely as you ask, so a mesh can be stored and animated at low resolution and rendered at high resolution.

## Patches

With tessellation, you no longer submit triangles. You submit **patches**: triangles or quads defined by **control points**. For each patch you provide **tessellation factors** that say how finely to subdivide it. The GPU's tessellator generates the new vertices, and a special vertex function computes the final position of each.

Metal's design differs from other APIs. There are no separate hull and domain shader stages. Instead:

1. A **compute kernel**, or the CPU, writes tessellation factors into a buffer.
2. The tessellator subdivides each patch according to its factors.
3. A **post-tessellation vertex function** runs once for every generated vertex.

## Tessellation factors

A quad patch has four **edge factors** and two **inside factors**. A triangle patch has three and one. A factor of 1 means no subdivision; 16 means the edge is split into 16 segments. Edge factors are separate from inside factors so that two neighboring patches can agree on their shared edge and leave no cracks, even when their interiors are subdivided differently.

A kernel that sets the same factor for every patch:

```cpp
#include <metal_stdlib>
using namespace metal;

kernel void compute_factors(device MTLQuadTessellationFactorsHalf *factors [[buffer(0)]],
                            constant float &level [[buffer(1)]],
                            uint patchID [[thread_position_in_grid]]) {
    factors[patchID].edgeTessellationFactor[0] = level;
    factors[patchID].edgeTessellationFactor[1] = level;
    factors[patchID].edgeTessellationFactor[2] = level;
    factors[patchID].edgeTessellationFactor[3] = level;
    factors[patchID].insideTessellationFactor[0] = level;
    factors[patchID].insideTessellationFactor[1] = level;
}
```

`MTLQuadTessellationFactorsHalf` is a built-in struct of six half floats, 12 bytes per patch:

```swift
let factorBuffer = device.makeBuffer(length: 12 * patchCount, options: .storageModePrivate)!
```

In a real renderer, the kernel computes each edge's factor from its distance to the camera or its length on screen. That is **adaptive tessellation**. Compute a factor per *edge* from that edge's own midpoint, so both patches sharing the edge get the same value.

## The pipeline

Control points go in an ordinary vertex buffer. The vertex descriptor says that the data advances per control point:

```swift
let vertexDescriptor = MTLVertexDescriptor()
vertexDescriptor.attributes[0].format = .float3
vertexDescriptor.attributes[0].offset = 0
vertexDescriptor.attributes[0].bufferIndex = 0
vertexDescriptor.layouts[0].stride = 12
vertexDescriptor.layouts[0].stepFunction = .perPatchControlPoint

let descriptor = MTLRenderPipelineDescriptor()
descriptor.vertexDescriptor = vertexDescriptor
descriptor.vertexFunction = library.makeFunction(name: "vertex_terrain")
descriptor.fragmentFunction = library.makeFunction(name: "fragment_terrain")
descriptor.colorAttachments[0].pixelFormat = view.colorPixelFormat
descriptor.depthAttachmentPixelFormat = .depth32Float

descriptor.tessellationFactorFormat = .half
descriptor.tessellationFactorStepFunction = .perPatch
descriptor.tessellationPartitionMode = .fractionalEven
descriptor.tessellationOutputWindingOrder = .counterClockwise
descriptor.maxTessellationFactor = 16
```

The **partition mode** controls how edges are split. `.integer` and `.pow2` snap to whole numbers, which causes visible popping as factors change. The fractional modes add new vertices gradually, so detail grows smoothly as the camera approaches. The maximum factor is 16 on older iOS devices and 64 on Macs and recent Apple GPUs.

## The post-tessellation vertex function

```cpp
struct ControlPoint {
    float3 position [[attribute(0)]];
};

struct PatchIn {
    patch_control_point<ControlPoint> controlPoints;
};

struct TerrainOut {
    float4 position [[position]];
    float2 uv;
    float height;
};

[[patch(quad, 4)]]
vertex TerrainOut vertex_terrain(PatchIn patch [[stage_in]],
                                 float2 patchCoord [[position_in_patch]],
                                 constant Uniforms &uniforms [[buffer(1)]],
                                 texture2d<float> heightMap [[texture(0)]],
                                 sampler s [[sampler(0)]]) {
    // Bilinear interpolation of the four corners.
    float3 top = mix(patch.controlPoints[0].position, patch.controlPoints[1].position, patchCoord.x);
    float3 bottom = mix(patch.controlPoints[3].position, patch.controlPoints[2].position, patchCoord.x);
    float3 position = mix(top, bottom, patchCoord.y);

    // Displace along y using a height map.
    float2 uv = position.xz / uniforms.terrainSize + 0.5;
    float height = heightMap.sample(s, uv, level(0)).r;
    position.y = height * uniforms.heightScale;

    TerrainOut out;
    out.position = uniforms.projection * uniforms.view * uniforms.model * float4(position, 1.0);
    out.uv = uv;
    out.height = height;
    return out;
}
```

- `[[patch(quad, 4)]]` declares a quad patch with four control points.
- `[[position_in_patch]]` is where the generated vertex lies within the patch: a `float2` from 0 to 1 for quads, and a `float3` of barycentric weights for triangles.
- Vertex functions cannot compute mip levels automatically, so texture samples name the level.

The function decides what the patch *means*. Here it is a flat quad displaced by a height map. Interpret sixteen control points as a bicubic Bézier patch and you get smooth curved surfaces from a coarse cage.

## Drawing

```swift
// 1. Compute pass: fill the factor buffer.
let compute = commandBuffer.makeComputeCommandEncoder()!
compute.setComputePipelineState(factorPipeline)
compute.setBuffer(factorBuffer, offset: 0, index: 0)
compute.setBytes(&level, length: MemoryLayout<Float>.stride, index: 1)
compute.dispatchThreads(MTLSize(width: patchCount, height: 1, depth: 1),
                        threadsPerThreadgroup: MTLSize(width: factorPipeline.threadExecutionWidth,
                                                       height: 1, depth: 1))
compute.endEncoding()

// 2. Render pass: draw the patches.
encoder.setRenderPipelineState(terrainPipeline)
encoder.setVertexBuffer(controlPointBuffer, offset: 0, index: 0)
encoder.setTessellationFactorBuffer(factorBuffer, offset: 0, instanceStride: 0)
encoder.setVertexTexture(heightMap, index: 0)
encoder.setVertexSamplerState(samplerState, index: 0)
encoder.setTriangleFillMode(.lines)      // to see the subdivision
encoder.drawPatches(numberOfPatchControlPoints: 4,
                    patchStart: 0,
                    patchCount: patchCount,
                    patchIndexBuffer: nil,
                    patchIndexBufferOffset: 0,
                    instanceCount: 1,
                    baseInstance: 0)
```

Textures and samplers for the vertex stage have their own binding calls, `setVertexTexture` and `setVertexSamplerState`.

## Normals for displaced surfaces

Displacement changes the surface, so the original normals are wrong. For a height map, compute the normal from neighboring heights, in the vertex function or per fragment:

```cpp
float2 texel = 1.0 / float2(heightMap.get_width(), heightMap.get_height());
float left  = heightMap.sample(s, uv - float2(texel.x, 0)).r;
float right = heightMap.sample(s, uv + float2(texel.x, 0)).r;
float down  = heightMap.sample(s, uv - float2(0, texel.y)).r;
float up    = heightMap.sample(s, uv + float2(0, texel.y)).r;
float3 normal = normalize(float3(left - right, 2.0 * texel.x * terrainSize / heightScale, down - up));
```

## Uses

- **Terrain** with continuous level of detail.
- **Displacement mapping**: real geometric detail with correct silhouettes and shadows, where [parallax mapping](../advanced-lighting/parallax-mapping.html) only fakes it.
- **Smooth surfaces**: subdivision surfaces and Bézier patches for characters and vehicles.

On recent hardware, mesh shaders offer another route to the same goals with more control. Tessellation remains the simplest way to get adaptive detail and is supported on every Apple GPU.

## Exercises

- Animate the tessellation level and watch the wireframe refine.
- Compute per-edge factors from the camera distance in the kernel.
- Compare `.integer` and `.fractionalEven` while moving the camera.
