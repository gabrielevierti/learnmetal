# Hello View

Time for the first Metal code: a renderer that clears the window to a color every frame. It draws no geometry, but it contains the complete skeleton of a frame, and every later chapter only adds to it.

<!-- cpp -->

!!! note "Reading this chapter in C++"
    There is no `MTKView` or delegate in metal-cpp. Your renderer keeps the `CAMetalLayer` from [Project Setup](project-setup.html), and `main.cpp` calls `renderer.draw()` once per loop. Where the text says `view.currentDrawable`, you call `layer->nextDrawable()`. Where it says `view.currentRenderPassDescriptor`, you fill in an `MTL::RenderPassDescriptor` yourself, which makes the load and store actions explained below visible in your own code.

<!-- /cpp -->

## The renderer

Create `Renderer.swift`:

```swift
import MetalKit

final class Renderer: NSObject, MTKViewDelegate {
    let device: MTLDevice
    let commandQueue: MTLCommandQueue

    init?(view: MTKView) {
        guard let device = MTLCreateSystemDefaultDevice(),
              let commandQueue = device.makeCommandQueue() else {
            return nil
        }
        self.device = device
        self.commandQueue = commandQueue
        super.init()

        view.device = device
        view.colorPixelFormat = .bgra8Unorm
        view.clearColor = MTLClearColor(red: 0.2, green: 0.3, blue: 0.3, alpha: 1.0)
        view.delegate = self
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {
        // Called when the view is resized. We will need it for the projection matrix later.
    }

    func draw(in view: MTKView) {
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let drawable = view.currentDrawable,
              let commandBuffer = commandQueue.makeCommandBuffer(),
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else {
            return
        }

        // Draw calls will go here.

        encoder.endEncoding()
        commandBuffer.present(drawable)
        commandBuffer.commit()
    }
}
```

Run it. You should see a window filled with dark teal.

## The device and the queue

`MTLCreateSystemDefaultDevice()` returns the GPU the system recommends. On Apple silicon there is only one. Everything else is created from this device.

The **command queue** is created once and kept for the lifetime of the app. It guarantees that the command buffers you commit are executed in order.

## Configuring the view

- `view.device` tells the view which GPU its textures live on. Without it nothing is drawn.
- `colorPixelFormat` is the format of the texture shown on screen. `.bgra8Unorm` means four 8-bit channels stored as blue, green, red, alpha, read by shaders as floats from 0 to 1. This is the view's default; we set it explicitly because we will change it in the [Gamma Correction](../advanced-lighting/gamma-correction.html) chapter.
- `clearColor` is the color the drawable is filled with at the start of each frame.

## Anatomy of a frame

`draw(in:)` is called once per display refresh, typically 60 or 120 times per second. Four things happen in it.

**1. Get a render pass descriptor.** A render pass is a batch of drawing that targets one set of textures, its **attachments**. `currentRenderPassDescriptor` is a ready-made descriptor whose color attachment is this frame's drawable texture. For each attachment a descriptor also holds:

- a **load action**: what to do with the existing contents when the pass begins (`.clear`, `.load`, or `.dontCare`),
- a **store action**: what to do with the result when it ends (`.store`, `.dontCare`, or a multisample resolve).

The view's descriptor uses `.clear` with your `clearColor`, and `.store`. That is why we get a colored window without drawing anything: clearing is part of beginning the pass.

!!! note "Coming from OpenGL"
    There is no `glClear` call. Clearing is a property of the render pass, and choosing load and store actions well matters for performance on tile-based GPUs, since each one can save or cost a full copy of the texture.

**2. Create a command buffer and an encoder.** The command buffer stores the encoded commands for this frame. The render command encoder translates your calls (set pipeline, set buffer, draw) into GPU commands for this one pass.

**3. End encoding.** You must call `endEncoding()` before creating another encoder or committing. Forgetting it is a validation error.

**4. Present and commit.** `present(drawable)` schedules the drawable to be shown as soon as the GPU finishes this command buffer. `commit()` hands the buffer to the queue. The call returns immediately; the GPU works asynchronously.

## Drawables are scarce

`currentDrawable` comes from a small pool, usually three textures. If all are in use, the call blocks until one is free, and it can return `nil`. That is why the method starts with a `guard` and simply skips the frame when anything is missing. Hold on to a drawable for as short a time as possible and never store it.

## Continuous or on demand

By default `MTKView` redraws continuously at `preferredFramesPerSecond`. For an editor-style app that only changes on input you can set `view.isPaused = true` and `view.enableSetNeedsDisplay = true`, then request frames with `setNeedsDisplay`. A game or an animation keeps the default.

## Exercises

- Change the clear color every frame using `CACurrentMediaTime()` and `sin` so the window pulses.
- Print `view.drawableSize` in `mtkView(_:drawableSizeWillChange:)` and resize the window. Notice that the size is in pixels, not points: on a Retina display it is twice the window size.
