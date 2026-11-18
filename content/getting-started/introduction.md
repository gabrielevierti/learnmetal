# Introduction

Before drawing anything, it helps to know what Metal is, what it is not, and how its pieces fit together. This chapter is all concepts and no code. The next one opens Xcode.

## What Metal is

Metal is Apple's low-level API for talking to the GPU. It covers two jobs:

- **Rendering**: turning triangles into pixels, which is what most of this site is about.
- **Compute**: running general-purpose parallel code on the GPU, which we reach in the [Beyond](../beyond/compute-shaders.html) section.

It runs on macOS, iOS, iPadOS, tvOS and visionOS, and it is the only first-class graphics API on those platforms. OpenGL and OpenCL have been deprecated there since 2018. SceneKit, RealityKit, SpriteKit, Core Animation, and game engines like Unity and Unreal all sit on top of Metal when running on Apple hardware.

Metal is *low-level* in the sense that it exposes how a GPU really works: you allocate buffers, describe pipelines, and record commands yourself. It is also noticeably friendlier than Vulkan or Direct3D 12. There is far less boilerplate, sensible defaults exist, and the debugging tools in Xcode are excellent.

## The objects you will meet

Almost everything in Metal is created from one object, the **device**, and nearly every type name starts with `MTL`. The cast is small:

| Object | Role |
| --- | --- |
| `MTLDevice` | The GPU. Factory for everything else. |
| `MTLCommandQueue` | An ordered line of work waiting for the GPU. |
| `MTLCommandBuffer` | One batch of work, usually one frame. |
| `MTLRenderCommandEncoder` | Writes draw commands for one render pass into a command buffer. |
| `MTLRenderPassDescriptor` | Says which textures a pass draws into and how they start and end. |
| `MTLRenderPipelineState` | A compiled vertex + fragment shader pair plus fixed configuration. |
| `MTLBuffer` | A block of memory the GPU can read: vertices, indices, uniforms. |
| `MTLTexture` | An image the GPU can read from or draw into. |
| `MTLSamplerState` | How a texture is filtered and wrapped when read. |
| `MTLDepthStencilState` | How depth and stencil tests behave. |
| `MTLLibrary` / `MTLFunction` | Compiled shader code and one function inside it. |

A frame always has the same shape:

1. Ask the command queue for a command buffer.
2. Create a render command encoder for a render pass.
3. Set state (pipeline, buffers, textures) and issue draw calls.
4. End encoding, ask to present the result on screen, and commit the command buffer.

Nothing reaches the GPU until you commit. Encoding is just writing a to-do list.

## State objects instead of a state machine

!!! note "Coming from OpenGL"
    OpenGL is one big global state machine: you bind things to a context and flip switches with `glEnable`. Metal has no global state at all. Expensive configuration is baked ahead of time into immutable objects (pipeline states, depth-stencil states, sampler states), and cheap per-draw state is set on an encoder that only lives for one pass. When an encoder ends, its state is gone.

This design is the main reason Metal is fast and predictable. Compiling shaders and validating configuration happen once when you create a state object, not unpredictably in the middle of a frame.

## Shaders

Shaders are small programs that run on the GPU. In Metal they are written in the **Metal Shading Language** (MSL), which is C++14 with some features removed and vector, matrix and texture types added. If you have written GLSL or HLSL, you can read MSL immediately.

Xcode compiles every `.metal` file in your project at build time into a single `default.metallib`, so shader syntax errors show up as ordinary build errors.

## Apple GPUs

Every current Apple device uses Apple silicon, whose GPUs are **tile-based deferred renderers** with **unified memory** shared by the CPU and GPU. You do not need to understand either yet, but they explain a few Metal features you will meet later: load and store actions, memoryless textures, and shared storage mode. Older Intel Macs with AMD or Intel GPUs also run Metal, with a few differences that are pointed out where they matter.

## Versions

The Metal API has grown through numbered generations. Everything in this series uses the long-established core API (`MTLCommandQueue`, `MTLRenderCommandEncoder`, and friends), which runs on all Metal-capable devices and is what almost all existing code, samples and answers online use. Apple has also introduced a newer set of interfaces under the name Metal 4, with types prefixed `MTL4`, aimed at engines that need explicit control. The concepts carry over directly, so learn the core API first; the [Metal 4](../apple-platforms/metal-4.html) chapter shows what changes.

## How to read this series

Go in order. Every chapter assumes the code from the previous one. Type the code yourself instead of pasting it. Change numbers and break things on purpose, then read what Xcode tells you. The official [Metal documentation](https://developer.apple.com/documentation/metal) and the [Metal Shading Language Specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf) are the references to keep open in another tab.
