# Compute Shaders

A GPU is a massively parallel computer that happens to be good at drawing triangles. **Compute functions**, called kernels in Metal, let you use that power for anything: image processing, physics, particle systems, simulations, culling, machine learning. They run outside the render pipeline, with no vertices or fragments, only data in and data out.

In Metal, compute is not an add-on. It uses the same device, command buffers, buffers, textures and shading language as rendering, so results flow between the two with no copying.

## A first kernel: image processing

A kernel is a function marked `kernel` that returns `void`. It is executed once for every point in a grid that you define. For an image, the grid is the pixels:

```cpp
#include <metal_stdlib>
using namespace metal;

kernel void grayscale(texture2d<float, access::read>  input  [[texture(0)]],
                      texture2d<float, access::write> output [[texture(1)]],
                      uint2 gid [[thread_position_in_grid]]) {
    float4 color = input.read(gid);
    float gray = dot(color.rgb, float3(0.2126, 0.7152, 0.0722));
    output.write(float4(float3(gray), color.a), gid);
}
```

- Textures declare how they are accessed: `access::read`, `access::write` or `access::read_write`. A texture that a kernel writes to must be created with `.shaderWrite` usage.
- `[[thread_position_in_grid]]` is the coordinate of this invocation, here the pixel.
- There is no sampler: `read` and `write` address exact texels. You can still pass a sampler and call `sample` with normalized coordinates when you want filtering.

## Running it

```swift
let function = library.makeFunction(name: "grayscale")!
let computePipeline = try device.makeComputePipelineState(function: function)
```

```swift
let encoder = commandBuffer.makeComputeCommandEncoder()!
encoder.setComputePipelineState(computePipeline)
encoder.setTexture(inputTexture, index: 0)
encoder.setTexture(outputTexture, index: 1)

let width = computePipeline.threadExecutionWidth
let height = computePipeline.maxTotalThreadsPerThreadgroup / width
encoder.dispatchThreads(MTLSize(width: inputTexture.width, height: inputTexture.height, depth: 1),
                        threadsPerThreadgroup: MTLSize(width: width, height: height, depth: 1))
encoder.endEncoding()
```

A compute encoder lives in a command buffer next to render encoders. A typical frame might run a compute pass to update particles, then a render pass that draws them, in one command buffer.

## Threads and threadgroups

The GPU executes the grid in batches called **threadgroups**. Threads in one group run together and can share a small amount of fast memory.

`dispatchThreads` takes the total grid size and a threadgroup size, and Metal handles grids that are not an exact multiple of the group size. It requires non-uniform threadgroup support, which every Apple silicon device has. The older `dispatchThreadgroups` takes a number of *groups* instead, so the grid is rounded up and the kernel must check for out-of-range coordinates itself:

```cpp
if (gid.x >= output.get_width() || gid.y >= output.get_height()) { return; }
```

The sizes used above, `threadExecutionWidth` wide and as tall as the maximum allows, are a good default for 2D work.

## A particle system

Buffers work in kernels just as textures do. Here every particle is moved by one thread:

```cpp
struct Particle {
    float3 position;
    float3 velocity;
    float life;
};

struct SimulationUniforms {
    float deltaTime;
    float3 gravity;
};

kernel void update_particles(device Particle *particles [[buffer(0)]],
                             constant SimulationUniforms &uniforms [[buffer(1)]],
                             uint id [[thread_position_in_grid]]) {
    Particle p = particles[id];

    p.velocity += uniforms.gravity * uniforms.deltaTime;
    p.position += p.velocity * uniforms.deltaTime;
    p.life -= uniforms.deltaTime;

    if (p.position.y < 0.0) {                 // bounce on the ground
        p.position.y = 0.0;
        p.velocity.y *= -0.6;
    }
    particles[id] = p;
}
```

The buffer is in the `device` address space because the kernel writes to it. The grid is one-dimensional:

```swift
encoder.setBuffer(particleBuffer, offset: 0, index: 0)
encoder.setBytes(&simulationUniforms, length: MemoryLayout<SimulationUniforms>.stride, index: 1)
encoder.dispatchThreads(MTLSize(width: particleCount, height: 1, depth: 1),
                        threadsPerThreadgroup: MTLSize(width: computePipeline.threadExecutionWidth,
                                                       height: 1, depth: 1))
```

Then bind the same buffer to an instanced billboard vertex function like the one in [Life Without Geometry Shaders](../advanced-metal/no-geometry-shaders.html), with its `Particle` struct changed to match this one, and draw. The particle data never leaves the GPU, and a million particles animate comfortably.

!!! warning "Data races"
    Threads run in parallel in no guaranteed order. Each thread must write only to its own element. If a thread reads data that another thread writes, as in a blur that reads neighbors, use separate input and output resources and swap them after each step. For shared counters, MSL provides atomic types such as `atomic_uint`.

## Where compute is used in a renderer

- **Post-processing**: blur, bloom, tone mapping, depth of field. A kernel avoids the full-screen triangle and can read and write any pixel.
- **Culling**: test object bounds against the view frustum and write a list of visible instances or an indirect command buffer.
- **Light assignment**: build per-tile or per-cluster light lists for forward rendering with many lights.
- **Precomputation**: the irradiance and prefiltered maps of the [IBL chapters](../pbr/diffuse-irradiance.html) can be generated by kernels writing directly to cube faces.
- **Simulation**: cloth, fluids, flocking.
- **Mesh generation**: terrain, marching cubes, skinning.

## Compute or fragment?

A full-screen fragment function and a kernel can often do the same job. Fragment functions benefit from the tile-based architecture when they write to render pass attachments, especially memoryless ones. Kernels are more flexible: arbitrary reads and writes, several outputs of different sizes, shared threadgroup memory. On Apple GPUs, prefer a fragment function when the result goes straight into the current render pass, and a kernel otherwise. Measure when it matters.

## Ready-made kernels

**Metal Performance Shaders** (MPS) is a library of tuned kernels: Gaussian blur, convolution, histogram, image scaling, matrix multiplication, and more. For standard image operations, use it before writing your own:

```swift
import MetalPerformanceShaders

let blur = MPSImageGaussianBlur(device: device, sigma: 8)
blur.encode(commandBuffer: commandBuffer, sourceTexture: source, destinationTexture: destination)
```

## Exercises

- Write a kernel that inverts an image and display the result.
- Port the box blur from the SSAO chapter to a kernel.
- Add an attractor point to the particle simulation that pulls particles toward the mouse.
