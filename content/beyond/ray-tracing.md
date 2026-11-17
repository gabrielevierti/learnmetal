# Ray Tracing

Rasterization answers one question very quickly: which triangle covers this pixel? Everything else, including shadows, reflections and ambient occlusion, has been an approximation layered on top: shadow maps, environment maps, screen-space tricks. Each breaks down somewhere.

**Ray tracing** answers a more general question: what does a ray starting *here* and going *that way* hit first? With that one operation, shadows, reflections and occlusion become exact and almost trivial to express. Metal has a ray tracing API that runs on all Apple silicon, with hardware acceleration on recent chips.

This chapter is an introduction. The goal is to understand the pieces and trace your first rays, then add ray traced shadows to the rasterized renderer you already have.

## Acceleration structures

Testing a ray against every triangle in a scene is hopeless. An **acceleration structure** organizes the triangles in a tree of bounding boxes, so a ray can skip almost all of them. Metal builds and traverses this structure for you.

There are two levels:

- A **primitive acceleration structure** holds the triangles of one mesh.
- An **instance acceleration structure** holds many instances of primitive structures, each with its own transform. Moving an object means updating a matrix and refitting the top level, not rebuilding the mesh.

Check for support first:

```swift
guard device.supportsRaytracing else { /* fall back to shadow maps */ return }
```

## Building a primitive structure

Describe the geometry using the vertex and index buffers you already have:

```swift
let geometry = MTLAccelerationStructureTriangleGeometryDescriptor()
geometry.vertexBuffer = mesh.vertexBuffers[0].buffer
geometry.vertexBufferOffset = mesh.vertexBuffers[0].offset
geometry.vertexStride = 32                       // positions are at offset 0
geometry.indexBuffer = submesh.indexBuffer.buffer
geometry.indexBufferOffset = submesh.indexBuffer.offset
geometry.indexType = submesh.indexType
geometry.triangleCount = submesh.indexCount / 3

let descriptor = MTLPrimitiveAccelerationStructureDescriptor()
descriptor.geometryDescriptors = [geometry]
```

Building happens on the GPU, through a dedicated encoder:

```swift
let sizes = device.accelerationStructureSizes(descriptor: descriptor)
let accelerationStructure = device.makeAccelerationStructure(size: sizes.accelerationStructureSize)!
let scratch = device.makeBuffer(length: sizes.buildScratchBufferSize, options: .storageModePrivate)!

let commandBuffer = commandQueue.makeCommandBuffer()!
let encoder = commandBuffer.makeAccelerationStructureCommandEncoder()!
encoder.build(accelerationStructure: accelerationStructure,
              descriptor: descriptor,
              scratchBuffer: scratch,
              scratchBufferOffset: 0)
encoder.endEncoding()
commandBuffer.commit()
```

Build static geometry once at load time. The same encoder can **compact** a structure to save memory and **refit** one after vertices move.

## Intersecting rays in a shader

Ray tracing in Metal is not a separate pipeline. Any shader, whether a kernel or a fragment function, can receive an acceleration structure and shoot rays into it.

```cpp
#include <metal_stdlib>
using namespace metal;
using namespace raytracing;

kernel void trace(texture2d<float, access::write> output [[texture(0)]],
                  constant CameraUniforms &camera [[buffer(0)]],
                  primitive_acceleration_structure scene [[buffer(1)]],
                  uint2 gid [[thread_position_in_grid]]) {
    // A ray through this pixel.
    float2 size = float2(output.get_width(), output.get_height());
    float2 ndc = (float2(gid) + 0.5) / size * 2.0 - 1.0;
    ndc.y = -ndc.y;

    ray r;
    r.origin = camera.position;
    r.direction = normalize(camera.forward
                          + ndc.x * camera.right * camera.tanHalfFov * camera.aspect
                          + ndc.y * camera.up * camera.tanHalfFov);
    r.min_distance = 0.001;
    r.max_distance = INFINITY;

    intersector<triangle_data> i;
    intersection_result<triangle_data> hit = i.intersect(r, scene);

    float3 color = float3(0.1, 0.1, 0.15);                 // background
    if (hit.type == intersection_type::triangle) {
        // Visualize the barycentric coordinates of the hit.
        float2 b = hit.triangle_barycentric_coord;
        color = float3(1.0 - b.x - b.y, b.x, b.y);
    }
    output.write(float4(color, 1.0), gid);
}
```

```swift
computeEncoder.setAccelerationStructure(accelerationStructure, bufferIndex: 1)
```

The intersection result tells you the distance to the hit, which primitive and which geometry were hit, and the barycentric coordinates of the hit point within the triangle. With the primitive index you look up the triangle's vertices in your own buffers and interpolate normals and texture coordinates. Metal can also store small per-primitive data inside the structure to make that lookup cheaper.

Run this kernel, show the output texture with the full-screen triangle, and you have a ray traced image of your mesh with no rasterization involved.

## Hybrid rendering: ray traced shadows

A full path tracer is a project of its own. The most practical use of ray tracing is **hybrid**: rasterize the scene as before, and use rays only for the effects that rasterization does badly.

Shadows are the easiest win. In the lighting fragment function, shoot one ray from the surface toward the light. If it hits anything, the point is in shadow:

```cpp
static float traceShadow(float3 worldPosition, float3 normal, float3 lightPosition,
                         primitive_acceleration_structure scene) {
    float3 toLight = lightPosition - worldPosition;
    float distance = length(toLight);

    ray r;
    r.origin = worldPosition + normal * 0.001;     // step off the surface
    r.direction = toLight / distance;
    r.min_distance = 0.001;
    r.max_distance = distance;

    intersector<triangle_data> i;
    i.accept_any_intersection(true);               // any hit will do
    return i.intersect(r, scene).type == intersection_type::none ? 1.0 : 0.0;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              primitive_acceleration_structure scene [[buffer(3)]]) {
    ...
    float lit = traceShadow(in.worldPosition, normalize(in.normal), light.position, scene);
    color += lit * (diffuse + specular);
}
```

```swift
encoder.setFragmentAccelerationStructure(accelerationStructure, bufferIndex: 3)
```

Compare with [Shadow Mapping](../advanced-lighting/shadow-mapping.html) and [Point Shadows](../advanced-lighting/point-shadows.html): no extra passes, no shadow textures, no bias tuning, no resolution limit, and it works for any type of light. `accept_any_intersection(true)` lets traversal stop at the first hit, which makes shadow rays cheap.

The same pattern gives:

- **Reflections**: trace along `reflect(-V, N)` and shade the hit point.
- **Ambient occlusion**: trace a few short rays in the hemisphere above the surface and count the hits. Real occlusion, replacing [SSAO](../advanced-lighting/ssao.html).
- **Soft shadows**: aim rays at random points on an area light and average over frames.

## Noise and denoising

One ray per pixel gives hard shadows and mirror reflections. Soft effects need many rays in random directions, and a real-time budget allows only a few per pixel. The result is noisy. The standard remedy is to **accumulate** results over several frames and to **denoise**. Metal Performance Shaders includes `MPSSVGFDenoiser`, and MetalFX offers denoised upscaling on recent systems.

## Going further

- **Instance acceleration structures** for scenes with many moving objects (`MTLInstanceAccelerationStructureDescriptor`).
- **Intersection functions** for custom primitives such as spheres and curves, and for alpha-tested geometry like foliage.
- **Path tracing**: follow rays through several bounces to compute global illumination. Apple's sample code "Accelerating ray tracing using Metal" is a compact, readable path tracer and the natural next step.

## The end, and the beginning

This is the last chapter. You started with an empty view and now have the vocabulary to read any Metal sample, engine source or graphics paper. Pick something you want to see on screen and build it. Read Apple's sample code, watch the Metal sessions from WWDC, and keep the frame debugger open. There is always one more technique to learn, and you now have the foundation to learn it.
