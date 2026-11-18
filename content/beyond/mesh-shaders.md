# Mesh Shaders

A vertex function receives one vertex and returns one vertex. It cannot create geometry, and it cannot throw a whole object away. A **mesh shader** pipeline replaces the vertex stage with two programmable stages that can do both, entirely on the GPU. It is Metal's answer to the geometry shaders of other APIs, and since Metal 4 it is also the recommended replacement for tessellation.

## Two new stages

- The **object stage** runs once per object, or per cluster of triangles. It decides whether that object is visible, how much detail it deserves, and how many meshes to launch for it. It can pass a small block of data, the **payload**, to the next stage. This stage is optional.
- The **mesh stage** runs once per mesh and writes the vertices, the indices and the number of primitives of a small mesh. The rasterizer then takes over as usual, and the fragment function does not change.

Both stages run like compute kernels: you dispatch a grid of threadgroups, and each thread knows its own index.

A small mesh of at most a few hundred triangles is called a **meshlet**. Splitting a large model into meshlets ahead of time, and culling them in the object stage, is the main use of this pipeline: triangles that cannot be seen never reach the rasterizer.

## The mesh function

The output type is a `mesh` template: the vertex type, the per-primitive type, the maximum number of vertices and primitives, and the topology.

```cpp
#include <metal_stdlib>
using namespace metal;

struct VertexOut {
    float4 position [[position]];
    float3 color;
};

struct PrimitiveOut {
    float shade;
};

using QuadMesh = metal::mesh<VertexOut, PrimitiveOut, 4, 2, metal::topology::triangle>;

struct Uniforms {
    float4x4 viewProjection;
    float time;
};

[[mesh]] void mesh_main(QuadMesh output,
                        constant Uniforms &uniforms [[buffer(0)]],
                        uint3 group [[threadgroup_position_in_grid]],
                        uint thread [[thread_index_in_threadgroup]]) {
    // One threadgroup makes one quad. Its position in the grid places the quad.
    float3 center = float3(float(group.x) - 16.0, 0.0, float(group.y) - 16.0) * 1.5;

    // Four threads: each writes one vertex.
    float2 corner = float2(thread & 1u, thread >> 1u) - 0.5;
    VertexOut v;
    v.position = uniforms.viewProjection * float4(center + float3(corner.x, sin(uniforms.time + center.x) * 0.3, corner.y), 1.0);
    v.color = float3(corner + 0.5, 0.5);
    output.set_vertex(thread, v);

    if (thread == 0u) {
        // Two triangles: 0-1-2 and 2-1-3.
        output.set_index(0, 0); output.set_index(1, 1); output.set_index(2, 2);
        output.set_index(3, 2); output.set_index(4, 1); output.set_index(5, 3);
        PrimitiveOut p;
        p.shade = 1.0;
        output.set_primitive(0, p);
        p.shade = 0.8;
        output.set_primitive(1, p);
        output.set_primitive_count(2);
    }
}
```

`set_primitive_count` is what makes the stage flexible: write 0 and the mesh produces nothing. The fragment function receives the interpolated vertex data and, if it asks for it, the per-primitive data.

```cpp
struct FragmentIn {
    VertexOut vertex;
    PrimitiveOut primitive;
};

fragment float4 fragment_main(FragmentIn in) {
    return float4(in.vertex.color * in.primitive.shade, 1.0);
}
```

## The pipeline and the draw call

The pipeline uses its own descriptor type. There is no vertex descriptor, because there are no vertex buffers: the mesh function reads whatever buffers it likes.

```swift
let descriptor = MTLMeshRenderPipelineDescriptor()
descriptor.meshFunction = library.makeFunction(name: "mesh_main")
descriptor.fragmentFunction = library.makeFunction(name: "fragment_main")
descriptor.colorAttachments[0].pixelFormat = view.colorPixelFormat
descriptor.depthAttachmentPixelFormat = .depth32Float

let (pipelineState, _) = try device.makeRenderPipelineState(descriptor: descriptor, options: [])
```

Buffers are bound per stage with `setMeshBuffer` and `setObjectBuffer`, and the draw call dispatches threadgroups instead of counting vertices.

```swift
encoder.setRenderPipelineState(pipelineState)
encoder.setMeshBuffer(uniformBuffer, offset: 0, index: 0)
encoder.drawMeshThreadgroups(
    MTLSize(width: 32, height: 32, depth: 1),                    // 1,024 quads
    threadsPerObjectThreadgroup: MTLSize(width: 1, height: 1, depth: 1),
    threadsPerMeshThreadgroup: MTLSize(width: 4, height: 1, depth: 1))
```

Without an object function, the grid you pass is the grid of mesh threadgroups.

## Adding the object stage

With an object function, the grid in the draw call is the grid of *object* threadgroups, and each of them decides how many mesh threadgroups to launch.

```cpp
struct Payload {
    float3 origin;
    uint detail;
};

[[object]] void object_main(object_data Payload &payload [[payload]],
                            mesh_grid_properties grid,
                            constant Uniforms &uniforms [[buffer(0)]],
                            uint3 group [[threadgroup_position_in_grid]]) {
    float3 origin = float3(float(group.x) - 4.0, 0.0, float(group.y) - 4.0) * 12.0;

    // Cull: is the center of this cluster inside the view volume?
    float4 clip = uniforms.viewProjection * float4(origin, 1.0);
    bool visible = clip.w > 0.0 && abs(clip.x) < clip.w * 1.3 && abs(clip.y) < clip.w * 1.3;
    if (!visible) {
        grid.set_threadgroups_per_grid(uint3(0, 0, 0));           // launch nothing
        return;
    }

    // Level of detail: fewer quads for far clusters.
    uint detail = clip.w < 30.0 ? 8u : (clip.w < 80.0 ? 4u : 2u);
    payload.origin = origin;
    payload.detail = detail;
    grid.set_threadgroups_per_grid(uint3(detail, detail, 1));
}
```

The mesh function receives the payload with `const object_data Payload &payload [[payload]]`. On the pipeline descriptor set `objectFunction`, `payloadMemoryLength` (the size of the payload struct) and `maxTotalThreadgroupsPerMeshGrid` (here 64).

## When to use them

- **Meshlet culling.** Per-cluster frustum, back-face and occlusion culling for dense models.
- **Procedural geometry.** Grass, hair, particles as quads, terrain patches: geometry that would otherwise need a compute pass and an intermediate buffer.
- **Level of detail on the GPU**, chosen per cluster and per frame.
- **Replacing geometry shaders** when porting from other APIs, and tessellation in Metal 4.

Mesh shaders need Metal 3: Apple silicon Macs, and iPhones and iPads with an A14 chip or later. Check `device.supportsFamily(.metal3)`. For an ordinary model drawn once, the vertex pipeline is simpler and just as fast.

## Exercises

- Change the number of quads by changing only the grid size in the draw call.
- Make the mesh function return zero primitives for every other quad, like a checkerboard.
- Add the object stage and color each cluster by its level of detail.
