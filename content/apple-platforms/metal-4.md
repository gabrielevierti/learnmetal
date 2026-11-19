# Metal 4

Metal 4, introduced in 2025, is the first large revision of Metal's core API. Nothing you have learned is obsolete: shaders, pipelines, textures, render passes and the frame structure are the same ideas. What changes is who is responsible for what. Metal 4 does less behind your back, so a large renderer spends less CPU time and memory, and so that engines written for Direct3D 12 or Vulkan map onto it directly.

It runs on Apple silicon: Macs with M1 or later and iPhones and iPads with A14 or later, on the 2025 systems (macOS 26, iOS 26) and newer. Check at runtime, and keep the classic path as a fallback.

!!! warning "Read this as a map"
    This chapter explains the model and shows the shape of the code. The names follow Apple's documentation at the time of writing, and this part of Metal is young. Start real work from Apple's sample *Drawing a triangle with Metal 4*.

## Side by side with the Metal you know

The new types carry an `MTL4` prefix and live next to the old ones. The device, textures, buffers, libraries and render pipeline states are shared.

| Metal | Metal 4 |
|---|---|
| `MTLCommandQueue` | `MTL4CommandQueue` |
| `MTLCommandBuffer`, created by the queue, used once | `MTL4CommandBuffer`, created by the device, reused |
| memory managed by Metal | `MTL4CommandAllocator` |
| `MTLRenderCommandEncoder` | `MTL4RenderCommandEncoder` |
| compute, blit and acceleration structure encoders | `MTL4ComputeCommandEncoder` |
| `setVertexBuffer`, `setFragmentTexture`, ... | `MTL4ArgumentTable` |
| automatic retain and hazard tracking | residency sets and barriers |
| `device.makeRenderPipelineState` | `MTL4Compiler` |

You can adopt it gradually: one part of a renderer can submit to an `MTL4CommandQueue` while the rest keeps its `MTLCommandQueue`, with events to order the work between them.

## Command buffers and allocators

A Metal 4 command buffer is a long-lived object. You begin it with an **allocator**, which supplies the memory the encoded commands are written into, end it, and commit it to a queue. Then you begin it again. Keep one allocator per frame in flight and reset it when you come back to it.

```swift
let commandQueue = device.makeMTL4CommandQueue()!
let commandBuffer = device.makeCommandBuffer()!                       // an MTL4CommandBuffer
let allocators = (0..<3).map { _ in device.makeCommandAllocator()! }  // one per frame in flight
```

```swift
let allocator = allocators[frameNumber % 3]
allocator.reset()                                        // the GPU finished with this memory three frames ago
commandBuffer.beginCommandBuffer(allocator: allocator)

guard let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }
// ... encode draws ...
encoder.endEncoding()

commandBuffer.endCommandBuffer()
commandQueue.waitForDrawable(drawable)
commandQueue.commit([commandBuffer])
commandQueue.signalDrawable(drawable)
drawable.present()
```

The pass descriptor is an `MTL4RenderPassDescriptor`; `MTKView` offers one through `currentMTL4RenderPassDescriptor`. Because committing takes an array, several threads can each encode into their own command buffer, with their own allocator, and the buffers are submitted together. A render pass can even be suspended at the end of one encoder and resumed in the next, which replaces the parallel render encoder.

## Argument tables

In classic Metal every encoder keeps a table of bindings for every stage, and you fill it with `setVertexBuffer`, `setFragmentTexture` and their relatives. In Metal 4 the table is an object of its own. You size it for what your shaders use, fill it, and attach it to the stages that need it. The same table can serve many encoders and many frames.

```swift
let tableDescriptor = MTL4ArgumentTableDescriptor()
tableDescriptor.maxBufferBindCount = 2
tableDescriptor.maxTextureBindCount = 1
tableDescriptor.maxSamplerStateBindCount = 1
let arguments = try device.makeArgumentTable(descriptor: tableDescriptor)

arguments.setAddress(vertexBuffer.gpuAddress, index: 0)            // [[buffer(0)]]
arguments.setAddress(uniformBuffer.gpuAddress + UInt64(offset), index: 1)
arguments.setTexture(colorTexture.gpuResourceID, index: 0)         // [[texture(0)]]
arguments.setSamplerState(sampler.gpuResourceID, index: 0)
```

```swift
encoder.setRenderPipelineState(pipelineState)
encoder.setArgumentTable(arguments, stages: [.vertex, .fragment])
encoder.drawPrimitives(primitiveType: .triangle, vertexStart: 0, vertexCount: 3)
```

A binding is an address or a resource ID, not an object, and an offset is plain arithmetic on the address. The shader does not change: `[[buffer(1)]]` still means slot 1. This pairs naturally with the argument buffers of the [Advanced MSL](../advanced-metal/advanced-msl.html) chapter: put a whole scene's textures in one buffer, and bind that single buffer.

## Residency sets

Classic command buffers retain every resource they use and make sure it is available to the GPU. Metal 4 does neither. You keep your resources alive yourself, and you tell Metal which ones the GPU needs with a **residency set**.

```swift
let residencyDescriptor = MTLResidencySetDescriptor()
residencyDescriptor.initialCapacity = 64
let residencySet = try device.makeResidencySet(descriptor: residencyDescriptor)

residencySet.addAllocations([vertexBuffer, uniformBuffer, colorTexture])
residencySet.commit()                                    // apply the additions

commandQueue.addResidencySet(residencySet)               // every command buffer on this queue can use them
commandQueue.addResidencySet(metalLayer.residencySet)    // the drawables' textures
```

Build the set when you load a level, not every frame. A resource missing from every set is the classic Metal 4 mistake, and the result is undefined: a black object, or garbage.

## Barriers

Metal 4 does not track which pass writes a resource and which reads it. Inside one command buffer, stages of different passes may overlap. Where a later stage reads what an earlier one wrote, for example a fragment function sampling a texture a compute pass just filled, you add a **barrier** on the consuming encoder: it names the stages that must finish and the stages that must wait. Rendering to a texture in one pass and sampling it in the next is the everyday case. Metal's validation layer reports missing barriers, so keep it on while porting.

## Compiling pipelines

Pipeline states are created by a compiler object that you own, from descriptors that name functions without loading them first.

```swift
let compiler = try device.makeCompiler(descriptor: MTL4CompilerDescriptor())

let vertexFunction = MTL4LibraryFunctionDescriptor()
vertexFunction.library = library
vertexFunction.name = "vertex_main"
let fragmentFunction = MTL4LibraryFunctionDescriptor()
fragmentFunction.library = library
fragmentFunction.name = "fragment_main"

let descriptor = MTL4RenderPipelineDescriptor()
descriptor.vertexFunctionDescriptor = vertexFunction
descriptor.fragmentFunctionDescriptor = fragmentFunction
descriptor.colorAttachments[0].pixelFormat = .bgra8Unorm

let pipelineState = try compiler.makeRenderPipelineState(descriptor: descriptor)
```

The result is an ordinary `MTLRenderPipelineState`. Three additions make shader compilation easier to control: asynchronous variants that return a task you can prioritize; **flexible pipeline states**, where one compiled pipeline is specialized cheaply for different blend and attachment settings; and ahead-of-time compilation, where pipelines harvested from a play session are compiled at build time into an archive, so players never wait for a shader.

## What else arrived with it

- **One compute encoder** for kernels, blits and acceleration structure builds.
- **Machine learning in the frame**: an `MTL4MachineLearningCommandEncoder` runs a Core ML network on the GPU timeline, and the Shader ML API evaluates small networks inside a fragment function, for neural materials or learned upscaling.
- **Texture view pools** and **placement sparse** resources for streaming large worlds.
- **MetalFX frame interpolation and denoising**, described in the previous chapter.
- Tessellation is not part of the Metal 4 encoder; use [mesh shaders](../beyond/mesh-shaders.html).

## Should you use it?

For learning, and for an app with a few hundred draw calls, classic Metal is simpler and exactly as fast on the GPU. Its automatic retains, tracking and residency cost little at that scale and prevent a whole class of bugs. Metal 4 pays off when the CPU cost of encoding matters: thousands of draws, many threads, large streaming scenes, or an engine that already thinks in descriptor tables and barriers. Every concept in this book carries over unchanged, which is the reason to learn them first.

## Exercises

- List what `setFragmentTexture` did for you that an argument table does not.
- Port the Hello Triangle renderer to Metal 4, starting from Apple's sample project.
