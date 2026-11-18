# visionOS

On Apple Vision Pro most apps draw with RealityKit. When you want your own renderer, for a game engine or a visualization, you draw **fully immersive** content with Metal through a framework called **Compositor Services**. Your shaders and pipelines are the ones from this book. What is new is everything around the frame: there are two eyes, the camera is a person's head, and the deadline is strict.

## What is different

- **Two views.** Each frame is rendered once per eye, with a different view and projection matrix for each.
- **You do not own the camera.** The view matrix comes from the headset's tracked position, through ARKit.
- **You do not own the frame loop.** There is no `MTKView` and no display link. Compositor Services gives you frames, and tells you when to start working on each.
- **The system reprojects.** Just before display, the system warps your image to match the latest head position. To do that it needs your depth buffer, so depth must be correct for every pixel you draw.
- **Foveation.** The headset renders the periphery at a lower resolution. You get this almost for free, but it changes how viewports and post-processing work.
- **Latency is comfort.** A late frame is not a small stutter here. Aim for the display's rate, 90 frames per second or more, every frame.

## The app and the layer

The entry point is SwiftUI. An `ImmersiveSpace` whose content is a `CompositorLayer` hands you a `LayerRenderer`, the object that replaces the view. Start a dedicated render thread from there; never render on the main thread.

<!-- swift -->
```swift
import SwiftUI
import CompositorServices

struct LayerConfiguration: CompositorLayerConfiguration {
    func makeConfiguration(capabilities: LayerRenderer.Capabilities,
                           configuration: inout LayerRenderer.Configuration) {
        let foveation = capabilities.supportsFoveation
        let layouts = capabilities.supportedLayouts(options: foveation ? [.foveationEnabled] : [])

        configuration.layout = layouts.contains(.layered) ? .layered : .dedicated
        configuration.isFoveationEnabled = foveation
        configuration.colorFormat = .rgba16Float          // HDR
        configuration.depthFormat = .depth32Float
    }
}

@main
struct ImmersiveApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }                      // a window with a button that opens the space

        ImmersiveSpace(id: "Scene") {
            CompositorLayer(configuration: LayerConfiguration()) { layerRenderer in
                let renderer = Renderer(layerRenderer)
                let thread = Thread { renderer.renderLoop() }
                thread.name = "Render Thread"
                thread.start()
            }
        }
    }
}
```
<!-- /swift -->

<!-- cpp -->
The entry point of a visionOS app is always SwiftUI, so a small Swift file like the one below stays in a C++ project. Everything after that can be C++: Compositor Services has a C API (`cp_layer_renderer_t`, `cp_frame_t`, `cp_drawable_t`), which is what engines use. The Swift closure passes the layer renderer to a C function that starts your render thread.

```swift
ImmersiveSpace(id: "Scene") {
    CompositorLayer(configuration: LayerConfiguration()) { layerRenderer in
        engine_start(layerRenderer)          // a C function, declared in the bridging header
    }
}
```

There is no GLFW on visionOS, and metal-cpp needs a bridge: the C API returns Objective-C texture objects, which you cast to `MTL::Texture*` in an Objective-C++ file, as in the `glfw_bridge.mm` of the macOS starter.
<!-- /cpp -->

The **layout** decides how the two eyes' images are stored. `.dedicated` gives one texture per eye and needs two render passes. `.layered` gives one array texture with a slice per eye, and lets you draw both eyes in one pass. Prefer layered.

## The frame loop

The loop follows the state of the layer: wait while it is paused, render while it is running, and leave when it is invalidated.

<!-- swift -->
```swift
func renderLoop() {
    while true {
        switch layerRenderer.state {
        case .paused:      layerRenderer.waitUntilRunning()
        case .running:     autoreleasepool { renderFrame() }
        case .invalidated: return
        @unknown default:  return
        }
    }
}
```
<!-- /swift -->

A frame has two phases that you announce to the system. In the **update** phase you run everything that does not depend on where the head is: animation, physics, input. Then you sleep until the last sensible moment, ask for the head pose, and enter the **submission** phase, where you encode and commit. Waiting matters: the later you read the pose, the less the system has to correct.

<!-- swift -->
```swift
func renderFrame() {
    guard let frame = layerRenderer.queryNextFrame() else { return }

    frame.startUpdate()
    scene.update()                                         // nothing here may depend on the head pose
    frame.endUpdate()

    guard let timing = frame.predictTiming() else { return }
    LayerRenderer.Clock().wait(until: timing.optimalInputTime)

    frame.startSubmission()
    for drawable in frame.queryDrawables() {
        // Where will the head be when this frame is shown?
        let time = LayerRenderer.Clock.Instant.epoch
            .duration(to: drawable.frameTiming.presentationTime).timeInterval
        let anchor = worldTracking.queryDeviceAnchor(atTimestamp: time)
        drawable.deviceAnchor = anchor

        guard let commandBuffer = commandQueue.makeCommandBuffer() else { continue }
        draw(drawable, anchor: anchor, commandBuffer: commandBuffer)
        drawable.encodePresent(commandBuffer: commandBuffer)
        commandBuffer.commit()
    }
    frame.endSubmission()
}
```
<!-- /swift -->

<!-- cpp -->
With the C API the same frame reads as follows. Each call matches a Swift method one to one.

```cpp
void Engine::renderFrame() {
    cp_frame_t frame = cp_layer_renderer_query_next_frame(layerRenderer);
    if (frame == nullptr) { return; }

    cp_frame_timing_t timing = cp_frame_predict_timing(frame);
    if (timing == nullptr) { return; }

    cp_frame_start_update(frame);
    scene.update();                                        // nothing here may depend on the head pose
    cp_frame_end_update(frame);

    cp_time_wait_until(cp_frame_timing_get_optimal_input_time(timing));

    cp_frame_start_submission(frame);
    cp_drawable_array_t drawables = cp_frame_query_drawables(frame);
    for (size_t i = 0; i < cp_drawable_array_get_count(drawables); i++) {
        cp_drawable_t drawable = cp_drawable_array_get_drawable(drawables, i);

        // Where will the head be when this frame is shown?
        cp_frame_timing_t drawableTiming = cp_drawable_get_frame_timing(drawable);
        CFTimeInterval time = cp_time_to_cf_time_interval(cp_frame_timing_get_presentation_time(drawableTiming));
        ar_device_anchor_t anchor = ar_device_anchor_create();
        ar_world_tracking_provider_query_device_anchor_at_timestamp(worldTracking, time, anchor);
        cp_drawable_set_device_anchor(drawable, anchor);

        drawAndPresent(drawable, anchor);                  // encode, cp_drawable_encode_present, commit
    }
    cp_frame_end_submission(frame);
}
```
<!-- /cpp -->

`worldTracking` is an ARKit `WorldTrackingProvider` that you start once with `ARKitSession().run([worldTracking])`. Setting `deviceAnchor` on the drawable tells the system which pose you rendered for, so it can correct the difference.

## Two eyes, two matrices

Each drawable has a list of views, normally two. A view gives the eye's transform relative to the device, and the drawable computes the eye's projection. Both are different for each eye, and the projection is not symmetric, so do not build it from a field of view.

<!-- swift -->
```swift
let deviceTransform = anchor?.originFromAnchorTransform ?? matrix_identity_float4x4

var uniforms = [ViewUniforms]()
for (index, view) in drawable.views.enumerated() {
    let eyeToWorld = deviceTransform * view.transform
    uniforms.append(ViewUniforms(
        view: eyeToWorld.inverse,
        projection: drawable.computeProjection(viewIndex: index)))
}
```
<!-- /swift -->

<!-- cpp -->
In C++ read the same values with `cp_drawable_get_view`, `cp_view_get_transform` and `cp_drawable_compute_projection`, and the device transform with `ar_anchor_get_origin_from_anchor_transform`. The view matrix is `simd_inverse(simd_mul(deviceTransform, eyeTransform))`.
<!-- /cpp -->

visionOS uses **reverse-Z**: the projection maps the near plane to depth 1 and the far plane to 0. Clear depth to 0 and compare with `.greater`. Units are meters, and the origin is on the floor where the space was opened.

## Both eyes in one pass

With the layered layout the render pass targets an array texture. **Vertex amplification** runs the vertex function once per eye for each draw call and routes each result to its slice, so the scene is encoded once.

<!-- swift -->
```swift
let pass = MTLRenderPassDescriptor()
pass.colorAttachments[0].texture = drawable.colorTextures[0]
pass.colorAttachments[0].loadAction = .clear
pass.colorAttachments[0].storeAction = .store
pass.depthAttachment.texture = drawable.depthTextures[0]
pass.depthAttachment.loadAction = .clear
pass.depthAttachment.clearDepth = 0                        // reverse-Z: 0 is far
pass.depthAttachment.storeAction = .store                  // the system needs the depth to reproject
pass.renderTargetArrayLength = drawable.views.count
pass.rasterizationRateMap = drawable.rasterizationRateMaps.first     // foveation

let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: pass)!
encoder.setViewports(drawable.views.map { $0.textureMap.viewport })

var mappings = (0..<drawable.views.count).map {
    MTLVertexAmplificationViewMapping(viewportArrayIndexOffset: UInt32($0),
                                      renderTargetArrayIndexOffset: UInt32($0))
}
encoder.setVertexAmplificationCount(drawable.views.count, viewMappings: &mappings)
encoder.setVertexBytes(uniforms, length: MemoryLayout<ViewUniforms>.stride * uniforms.count, index: 1)
```
<!-- /swift -->

<!-- cpp -->
The render pass is built the same way with metal-cpp, from `cp_drawable_get_color_texture(drawable, 0)`, `cp_drawable_get_depth_texture(drawable, 0)`, `cp_drawable_get_view_count(drawable)` and `cp_drawable_get_rasterization_rate_map(drawable, 0)`. Then call `encoder->setViewports`, `encoder->setVertexAmplificationCount(count, mappings)` and bind the array of per-eye uniforms.
<!-- /cpp -->

The pipeline descriptor needs `maxVertexAmplificationCount = 2`, and the vertex function picks its matrices with the amplification index.

```cpp
struct ViewUniforms {
    float4x4 view;
    float4x4 projection;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             ushort eye [[amplification_id]],
                             constant ViewUniforms *views [[buffer(1)]],
                             constant ModelUniforms &model [[buffer(2)]]) {
    VertexOut out;
    float4 world = model.matrix * float4(in.position, 1.0);
    out.position = views[eye].projection * views[eye].view * world;
    out.worldPosition = world.xyz;
    return out;
}
```

Note what is stored: unlike on the Mac, the depth attachment uses `.store`, because the compositor reads it. This is the one place where the advice of the [tile-based GPU](tile-based-gpus.html) chapter is overruled.

## Practical notes

- **Foveation and post-processing.** With a rasterization rate map the texture is not uniform, so a full-screen pass that samples it must convert coordinates through the map. Start without post-processing.
- **Passthrough.** For mixed immersion, where your content appears in the person's room, clear to transparent black and write premultiplied alpha; the system composites the camera image behind you.
- **Input.** There are no keys or mouse. Pinches and gazes arrive as spatial events on the layer renderer, and hands through ARKit hand tracking.
- **The Simulator** does not support every layout or foveation. Check the capabilities instead of assuming, as the configuration above does.
- **Budget.** Two views at high resolution and 90 Hz leave a few milliseconds of GPU time. Forward rendering with MSAA, few passes and half-precision shaders is the usual choice.

## Exercises

- Draw the ten-cube scene of Getting Started two meters in front of the starting position.
- Give each eye a different clear color and check that the layers are routed correctly.
- Switch to the dedicated layout and render with two passes. Compare the CPU time of encoding.
