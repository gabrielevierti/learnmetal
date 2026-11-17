# Instancing

A field of grass, a forest, an asteroid belt: thousands of copies of the same mesh, each with a different transform. Issuing one draw call per copy wastes CPU time, because each call has a fixed cost no matter how small the mesh is. **Instancing** draws all copies with a single call.

## Instanced draw calls

Every draw method has a variant with an `instanceCount`:

```swift
encoder.drawPrimitives(type: .triangle,
                       vertexStart: 0,
                       vertexCount: 36,
                       instanceCount: 1000)

encoder.drawIndexedPrimitives(type: .triangle,
                              indexCount: submesh.indexCount,
                              indexType: submesh.indexType,
                              indexBuffer: submesh.indexBuffer.buffer,
                              indexBufferOffset: submesh.indexBuffer.offset,
                              instanceCount: 1000)
```

The GPU runs the vertex function for every vertex of every instance. The only difference between instances is the built-in `[[instance_id]]`, counting from 0. Everything that makes instances look different is derived from that number.

## Per-instance data in a buffer

Put one struct per instance into a buffer and index it with the instance ID:

```cpp
struct InstanceData {
    float4x4 model;
    float4 color;
};

vertex VertexOut vertex_instanced(VertexIn in [[stage_in]],
                                  uint instanceID [[instance_id]],
                                  constant Uniforms &uniforms [[buffer(1)]],
                                  const device InstanceData *instances [[buffer(2)]]) {
    InstanceData instance = instances[instanceID];

    VertexOut out;
    float4 world = instance.model * float4(in.position, 1.0);
    out.position = uniforms.projection * uniforms.view * world;
    out.worldPosition = world.xyz;
    out.normal = (instance.model * float4(in.normal, 0.0)).xyz;
    out.uv = in.uv;
    out.color = instance.color;
    return out;
}
```

Using the model matrix for the normal is only correct for rotations and uniform scales. Store a normal matrix per instance if you need non-uniform scaling.

```swift
struct InstanceData {
    var model: float4x4
    var color: SIMD4<Float>
}

let instanceBuffer = device.makeBuffer(length: MemoryLayout<InstanceData>.stride * instanceCount,
                                       options: .storageModeShared)!

let instances = instanceBuffer.contents().bindMemory(to: InstanceData.self, capacity: instanceCount)
for i in 0..<instanceCount {
    instances[i] = InstanceData(model: transforms[i], color: colors[i])
}
```

```swift
encoder.setVertexBuffer(instanceBuffer, offset: 0, index: 2)
```

!!! note "Coming from OpenGL"
    There is no need for instanced vertex attributes with divisors, and no limit on the size of per-instance data. A buffer and an index are enough. If you prefer attributes anyway, a vertex descriptor layout can advance once per instance: `layouts[1].stepFunction = .perInstance`.

## An asteroid field

Generate a ring of randomly placed, rotated and scaled rocks around a planet:

```swift
func makeAsteroidTransforms(count: Int, radius: Float, spread: Float) -> [float4x4] {
    (0..<count).map { i in
        let angle = Float(i) / Float(count) * 2 * .pi
        let offset = { Float.random(in: -spread...spread) }
        let position = Float3(sin(angle) * radius + offset(),
                              offset() * 0.4,
                              cos(angle) * radius + offset())
        let scale = Float.random(in: 0.05...0.25)
        let rotation = Float.random(in: 0...(2 * .pi))

        return float4x4(translation: position)
             * float4x4(rotation: rotation, axis: [0.4, 0.6, 0.8])
             * float4x4(scale: Float3(repeating: scale))
    }
}
```

Drawn with one call per rock, a few thousand asteroids already cost real CPU time each frame. Drawn instanced, a hundred thousand run smoothly, and the limit becomes how many triangles the GPU can fill.

## Animating instances

Since the instance buffer is shared memory, updating it is a plain write each frame. Use the ring-buffer scheme from [Advanced Data](advanced-data.html) so you do not overwrite data the GPU is still reading. For very large counts, moving the update itself to the GPU with a [compute function](../beyond/compute-shaders.html) removes the CPU from the loop entirely.

## Culling and the next step

Instancing draws every instance, visible or not. Large worlds cull on the CPU and write only visible instances to the buffer, or let the GPU do it: a compute pass tests each instance against the view frustum and writes the survivors into an **indirect command buffer**, a list of draw calls encoded on the GPU itself (`MTLIndirectCommandBuffer`). That technique, GPU-driven rendering, is beyond this series, but instancing is its first step.

## Exercises

- Draw a 100 × 100 grid of cubes with one call, coloring each by its instance ID.
- Make the asteroid ring rotate by passing a time uniform and rotating in the vertex function, with no CPU buffer updates.
