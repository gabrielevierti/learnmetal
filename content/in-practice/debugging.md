# Debugging

Graphics bugs are different from ordinary bugs. There is no stack trace for a black screen, and you cannot print from a fragment function. The good news is that Metal's tooling is among the best of any graphics API, and all of it is built into Xcode. Learning these tools early will save you days.

## Layer 1: API validation

**Metal API Validation** checks every call you make: mismatched pixel formats, missing buffers, wrong load actions, encoders left open. When something is wrong, the app stops at the offending call with a message that usually names the exact property:

```
-[MTLDebugRenderCommandEncoder setRenderPipelineState:]: failed assertion
`Set Render Pipeline State Validation
For color attachment 0, the render pipeline's pixelFormat (MTLPixelFormatBGRA8Unorm)
does not match the framebuffer's pixelFormat (MTLPixelFormatRGBA16Float).'
```

It is enabled by default when you run from Xcode (**Edit Scheme → Run → Diagnostics**). Never turn it off during development. It is disabled automatically in release builds, so it costs your users nothing.

## Layer 2: shader validation

In the same scheme panel, **Shader Validation** instruments your shaders to catch what API validation cannot see: reading past the end of a buffer, sampling a texture that was never bound, accessing an array out of bounds. Bad accesses are reported in the console with the function name and line. It slows rendering down, so enable it when a shader behaves strangely.

## Label everything

Every Metal object has a `label` property. Labels appear in validation messages, in the debugger and in Instruments. A message about "Scene HDR Color" is a lot more useful than one about `<AGXG14GFamilyTexture: 0x12f80a400>`.

```swift
sceneColor.label = "Scene HDR Color"
pipelineDescriptor.label = "PBR Opaque Pipeline"
commandBuffer.label = "Frame"
encoder.label = "Shadow Pass"
vertexBuffer.label = "Cube Vertices"
```

Inside an encoder, group related commands so they show up as a collapsible tree in the debugger:

```swift
encoder.pushDebugGroup("Draw Opaque Models")
for model in models {
    encoder.pushDebugGroup(model.name)
    model.draw(with: encoder)
    encoder.popDebugGroup()
}
encoder.popDebugGroup()

encoder.insertDebugSignpost("Before skybox")
```

## The GPU frame debugger

While your app runs, click the **camera** icon (Capture GPU Workload) in Xcode's debug bar. Xcode freezes one frame and lets you take it apart:

- **The navigator** lists every command buffer, pass and draw call, organized by your debug groups. Step through draws and watch the frame being built up one call at a time.
- **Attachments** shows the color, depth and stencil textures as they are after the selected draw. The current draw's geometry is outlined.
- **Bound resources** shows every buffer, texture and sampler bound for the selected draw. You can open a buffer and view its bytes laid out as your struct. This is the fastest way to find a uniform layout mismatch.
- **Geometry viewer** shows the mesh after the vertex function, in clip space, with each vertex's outputs. When an object is missing, look here first: you will see at once whether it is behind the camera, clipped, or collapsed to a point.
- **Shader debugger**: select a pixel, click **Debug**, and step through the fragment function's execution for that exact pixel, with the value of every variable on every line. The same works for a vertex. It is the closest thing to a breakpoint inside a shader.
- **Shader editing**: change shader code in the debugger and reload it to see the effect on the captured frame without rebuilding the app.
- **Dependency viewer** draws a graph of all passes and the textures flowing between them, with load and store actions. It makes redundant passes and unnecessary stores obvious.
- **Performance and memory**: per-pass and per-draw GPU time, and a list of every resource with its size.

You can also capture from code, to grab one specific frame:

```swift
let captureDescriptor = MTLCaptureDescriptor()
captureDescriptor.captureObject = device
try MTLCaptureManager.shared().startCapture(with: captureDescriptor)
// ...render a frame...
MTLCaptureManager.shared().stopCapture()
```

Programmatic capture needs the `MetalCaptureEnabled` key set to `YES` in Info.plist.

## The performance HUD

Metal can overlay a live graph of frame rate, frame time, GPU time and memory on any Metal app. Enable it in the scheme's options (**Show Graphics HUD**), or with the environment variable `MTL_HUD_ENABLED=1`. Keep it on while you work so that a sudden slowdown is noticed when it is introduced.

## Debugging by color

The oldest technique still works. When a value is in doubt, output it as a color:

```cpp
return float4(normal * 0.5 + 0.5, 1.0);        // normals
return float4(in.uv, 0.0, 1.0);                 // texture coordinates
return float4(float3(shadow), 1.0);             // a scalar
return float4(fract(in.worldPosition), 1.0);    // positions, as a repeating pattern
```

Remap values outside the 0 to 1 range first, or you only see black and white. Magenta is the traditional "this should never happen" color: `return float4(1, 0, 1, 1);` inside a branch tells you instantly whether it is taken.

## Command buffer errors

A command buffer can fail on the GPU, for example by running out of memory or timing out. Check in the completion handler:

```swift
commandBuffer.addCompletedHandler { buffer in
    if let error = buffer.error {
        print("Command buffer failed: \(error)")
    }
}
```

For more detail, create the buffer with `MTLCommandBufferDescriptor` and `errorOptions = .encoderExecutionStatus`. The error then reports which encoder, by label, was executing when the failure happened.

## Instruments

For performance questions that span many frames, such as stutters, CPU-GPU synchronization, and shader compilation hitches, profile with the **Metal System Trace** and **Game Performance** templates in Instruments. They show the CPU encoding, the GPU execution and the display's presentation of each frame on one timeline.

## A checklist for "nothing is drawn"

1. Is there a validation message in the console? Read it.
2. Capture a frame. Is the draw call there? If not, your code never issued it.
3. Open the geometry viewer. Are the vertices inside the clip volume?
4. Check the depth attachment and compare function. Is everything failing the depth test?
5. Check culling and winding. Try `setCullMode(.none)`.
6. Look at the bound buffers. Are the matrices sensible, or is the layout off?
7. Return a solid color from the fragment function. If that appears, the problem is in the shading.
8. Is the alpha zero with blending enabled?

Work from the outside in and the cause is usually found in minutes.
