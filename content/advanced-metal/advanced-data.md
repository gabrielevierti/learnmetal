# Advanced Data

Buffers and textures have been black boxes created with one call. This chapter opens them up: where their memory lives, how to update it efficiently every frame, and how to copy data around on the GPU.

## Buffers are just memory

An `MTLBuffer` is an untyped block of bytes. Metal attaches no meaning to it. The same buffer can hold vertices in its first half and uniforms in its second, and you say which part to use through the `offset` parameter when binding.

Create an empty buffer and fill it later:

```swift
let buffer = device.makeBuffer(length: 1024, options: .storageModeShared)!
```

`buffer.contents()` returns a raw pointer to the memory. Writing through it is the fastest way to update data:

```swift
let pointer = buffer.contents().bindMemory(to: Uniforms.self, capacity: 1)
pointer.pointee = uniforms
```

or for an array:

```swift
buffer.contents().copyMemory(from: vertices,
                             byteCount: MemoryLayout<Vertex>.stride * vertices.count)
```

## Storage modes

A resource's **storage mode** says who can access its memory.

| Mode | CPU access | GPU access | Notes |
| --- | --- | --- | --- |
| `.shared` | yes | yes | One copy in memory visible to both. The default for buffers on Apple silicon. |
| `.private` | no | yes | GPU only. Best for render targets and static data. |
| `.managed` | yes | yes | Two synchronized copies. Only meaningful on Macs with discrete GPUs. |
| `.memoryless` | no | during a pass | Textures only, Apple GPUs. Exists only while a render pass runs. |

Apple silicon has **unified memory**: the CPU and GPU share the same physical RAM. A shared buffer is not copied when the GPU uses it, so "uploading" data is nothing more than writing to memory. Rules of thumb:

- Data you rewrite every frame: `.shared`.
- Textures you render into and static meshes you never touch again: `.private`.
- Depth or multisample attachments that you do not keep: `.memoryless`.

## Updating uniforms safely

`setVertexBytes` is convenient but limited to 4 KB per call and copies the data each time. A real renderer keeps uniforms in buffers. There is one hazard: the GPU runs behind the CPU. If you overwrite a buffer for frame N+1 while the GPU is still drawing frame N, frame N reads the wrong data.

The standard cure is a small **ring of buffers**, one per frame in flight, with a semaphore that stops the CPU from getting too far ahead:

```swift
let maxFramesInFlight = 3
let frameSemaphore = DispatchSemaphore(value: maxFramesInFlight)
var uniformBuffers: [MTLBuffer] = []
var frameIndex = 0

// init
for _ in 0..<maxFramesInFlight {
    uniformBuffers.append(device.makeBuffer(length: MemoryLayout<Uniforms>.stride * maxObjects,
                                            options: .storageModeShared)!)
}
```

```swift
func draw(in view: MTKView) {
    frameSemaphore.wait()
    frameIndex = (frameIndex + 1) % maxFramesInFlight
    let uniformBuffer = uniformBuffers[frameIndex]

    guard let commandBuffer = commandQueue.makeCommandBuffer() else {
        frameSemaphore.signal()
        return
    }
    commandBuffer.addCompletedHandler { [frameSemaphore] _ in
        frameSemaphore.signal()
    }

    // Write all objects' uniforms into the buffer...
    let uniformsPointer = uniformBuffer.contents().bindMemory(to: Uniforms.self, capacity: maxObjects)
    for (i, object) in objects.enumerated() {
        uniformsPointer[i] = object.uniforms
    }

    // ...then bind once and move the offset per draw.
    encoder.setVertexBuffer(uniformBuffer, offset: 0, index: 1)
    for i in objects.indices {
        encoder.setVertexBufferOffset(MemoryLayout<Uniforms>.stride * i, index: 1)
        // draw object i
    }
    ...
}
```

`setVertexBufferOffset` is much cheaper than rebinding a buffer. One large buffer with per-object offsets is how thousands of draws stay fast. Make sure every early return after `wait()` signals the semaphore, or the app freezes after three frames.

## Copying on the GPU: the blit encoder

A third kind of encoder, next to render and compute, moves data between resources:

```swift
let blit = commandBuffer.makeBlitCommandEncoder()!

// Buffer to buffer
blit.copy(from: sourceBuffer, sourceOffset: 0,
          to: destinationBuffer, destinationOffset: 0,
          size: sourceBuffer.length)

// Texture to texture (same format and size)
blit.copy(from: sourceTexture, to: destinationTexture)

// Build the mipmap chain of a texture you rendered or filled yourself
blit.generateMipmaps(for: texture)

blit.endEncoding()
```

The blit encoder is also how you fill a `.private` resource: write the data into a shared staging buffer and blit it across.

## Reading data back

To read pixels back, the result has to be in CPU-visible memory after the GPU has finished:

```swift
let bytesPerRow = texture.width * 4
let readback = device.makeBuffer(length: bytesPerRow * texture.height, options: .storageModeShared)!

let blit = commandBuffer.makeBlitCommandEncoder()!
blit.copy(from: texture, sourceSlice: 0, sourceLevel: 0,
          sourceOrigin: MTLOrigin(x: 0, y: 0, z: 0),
          sourceSize: MTLSize(width: texture.width, height: texture.height, depth: 1),
          to: readback, destinationOffset: 0,
          destinationBytesPerRow: bytesPerRow,
          destinationBytesPerImage: bytesPerRow * texture.height)
blit.endEncoding()

commandBuffer.addCompletedHandler { _ in
    let pixels = readback.contents()   // valid now
}
commandBuffer.commit()
```

Never block the render loop with `waitUntilCompleted()` to get results. Use the completion handler.

## Texture descriptors in full

`MTLTextureDescriptor` has more to offer than width and height:

| Property | Use |
| --- | --- |
| `textureType` | `.type2D`, `.type2DArray`, `.typeCube`, `.type3D`, `.type2DMultisample`, and more. |
| `pixelFormat` | Channel layout and precision. |
| `mipmapLevelCount` | Number of mip levels. |
| `arrayLength` | Layers in an array texture. |
| `sampleCount` | Samples per pixel for multisampling. |
| `usage` | `.shaderRead`, `.shaderWrite`, `.renderTarget`, `.pixelFormatView`. Declare only what you need; it lets Metal optimize. |
| `storageMode` | As above. |

**Texture arrays** stack many same-sized images in one texture, indexed by layer in the shader with `texture2d_array<float>`. They replace texture atlases without the bleeding problems.

## Exercises

- Convert the ten-cube scene from `setVertexBytes` to the ring-buffer scheme.
- Render the scene to a texture, read it back, and save it as a PNG with Core Graphics.
