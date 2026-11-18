# MetalFX Upscaling

The cost of a frame grows with the number of pixels. **MetalFX** lets you render the scene at a lower resolution and produces a full-resolution image that looks close to one rendered natively. A game that renders 1280 × 720 and upscales to 2560 × 1440 shades a quarter of the pixels.

MetalFX offers two upscalers, and since 2025 a denoising upscaler for ray tracing and a frame interpolator.

| Effect | Needs | Use it when |
|---|---|---|
| Spatial scaler | The color image | You want the simplest integration, or have no motion vectors |
| Temporal scaler | Color, depth, motion vectors, camera jitter | You want the best quality, and anti-aliasing with it |
| Temporal denoised scaler | The above plus normals, albedo, roughness | The image is ray traced with few rays per pixel |
| Frame interpolator | Two frames, depth, motion vectors | You want a higher frame rate than you can render |

The scalers are available from macOS 13 and iOS 16 on devices with Apple silicon. The denoised scaler and the frame interpolator need the 2025 systems (macOS 26, iOS 26).

## Where it goes in the frame

Upscaling replaces nothing in your renderer. It is one more step, and its place matters.

1. Render the scene at low resolution into an HDR texture.
2. **Upscale** to the output resolution.
3. Post-process at full resolution: bloom, tone mapping.
4. Draw the user interface at full resolution, on top.

Text and interface elements must never go through the upscaler: draw them afterwards, at native resolution.

## The spatial scaler

It works on a single image, with no history. Create it once, and again whenever a size changes.

```swift
import MetalFX

let descriptor = MTLFXSpatialScalerDescriptor()
descriptor.inputWidth = renderWidth
descriptor.inputHeight = renderHeight
descriptor.outputWidth = outputWidth
descriptor.outputHeight = outputHeight
descriptor.colorTextureFormat = .rgba16Float
descriptor.outputTextureFormat = .rgba16Float
descriptor.colorProcessingMode = .hdr                 // the input is linear HDR, before tone mapping

guard let scaler = descriptor.makeSpatialScaler(device: device) else {
    fatalError("MetalFX spatial scaling is not supported on this device")
}
```

Each frame, hand it the textures and encode it into the command buffer, between your passes. It is not part of a render pass.

```swift
scaler.colorTexture = sceneTexture
scaler.outputTexture = upscaledTexture
scaler.encode(commandBuffer: commandBuffer)
```

The output texture must be created with the usage the scaler asks for in `outputTextureUsage`, and with `storageMode = .private`.

## The temporal scaler

The temporal scaler gathers detail from previous frames. Each frame you shift the whole image by a fraction of a pixel, the **jitter**, so that over several frames every pixel is sampled at many positions. The scaler lines up the old frames with the new one using **motion vectors**, and blends them. The result has more real detail than any single frame, and it is anti-aliased, so MSAA becomes unnecessary.

It needs three inputs beyond the color.

- **Depth**, from the same low-resolution pass.
- **Motion vectors**: for each pixel, how far the surface moved on screen since the last frame. Render them as an extra color attachment (`rg16Float`).
- **The jitter offset** you applied to the projection this frame.

```swift
let descriptor = MTLFXTemporalScalerDescriptor()
descriptor.inputWidth = renderWidth
descriptor.inputHeight = renderHeight
descriptor.outputWidth = outputWidth
descriptor.outputHeight = outputHeight
descriptor.colorTextureFormat = .rgba16Float
descriptor.depthTextureFormat = .depth32Float
descriptor.motionTextureFormat = .rg16Float
descriptor.outputTextureFormat = .rgba16Float

guard MTLFXTemporalScalerDescriptor.supportsDevice(device),
      let scaler = descriptor.makeTemporalScaler(device: device) else {
    fatalError("MetalFX temporal scaling is not supported on this device")
}
scaler.motionVectorScaleX = Float(renderWidth)        // our vectors are in uv units; the scaler wants pixels
scaler.motionVectorScaleY = Float(renderHeight)
```

### Jitter

Use a low-discrepancy sequence, such as Halton with bases 2 and 3, and move the projection by that sub-pixel amount.

```swift
func halton(_ index: Int, _ base: Int) -> Float {
    var f: Float = 1, result: Float = 0, i = index
    while i > 0 {
        f /= Float(base)
        result += f * Float(i % base)
        i /= base
    }
    return result
}

let jitter = SIMD2<Float>(halton(frameIndex % 8 + 1, 2) - 0.5,
                          halton(frameIndex % 8 + 1, 3) - 0.5)       // in pixels, -0.5 ... 0.5

// Shift clip space by that many pixels. Column 2 is multiplied by z, which cancels the divide by w.
var jittered = projection
jittered.columns.2.x += 2 * jitter.x / Float(renderWidth)
jittered.columns.2.y -= 2 * jitter.y / Float(renderHeight)
```

Whether the sign of each term is right depends on your projection convention. If the image shimmers or blurs when the camera is still, flip one sign at a time: with the correct signs a static scene converges to a sharp image in a few frames.

### Motion vectors

In the vertex function compute the clip-space position of the vertex in this frame and in the previous one, both **without** jitter, and pass them on. The fragment function turns them into a uv-space difference.

```cpp
struct SceneOut {
    float4 color  [[color(0)]];
    float2 motion [[color(1)]];
};

fragment SceneOut fragment_scene(VertexOut in [[stage_in]] /* ... */) {
    SceneOut out;
    out.color = shade(in);

    float2 current  = in.currentClip.xy  / in.currentClip.w;
    float2 previous = in.previousClip.xy / in.previousClip.w;
    // NDC to uv: scale by 0.5 and flip y. The vector points from this frame back to the previous one.
    out.motion = (previous - current) * float2(0.5, -0.5);
    return out;
}
```

Every moving object needs its previous model matrix, and the camera its previous view-projection matrix.

### Encoding

```swift
scaler.colorTexture = sceneTexture
scaler.depthTexture = depthTexture
scaler.motionTexture = motionTexture
scaler.outputTexture = upscaledTexture
scaler.jitterOffsetX = jitter.x
scaler.jitterOffsetY = jitter.y
scaler.reset = cameraDidCut                            // true for one frame after a teleport or scene change
scaler.encode(commandBuffer: commandBuffer)
```

Set `isDepthReversed` if you use reverse-Z. Set `reset` whenever the history is useless, or ghosts of the old scene will linger.

## Getting the quality right

- **Texture detail.** A low-resolution render picks blurrier mip levels. Give your samplers a negative LOD bias of `log2(renderWidth / outputWidth)`, for example -1 when upscaling 2×, so textures keep their full-resolution sharpness.
- **Ghosting** behind moving objects means wrong or missing motion vectors. Check animated, skinned and instanced objects first.
- **Transparent and particle effects** have no motion vectors of their own. Mark them in the scaler's **reactive mask** so it trusts the new frame more there.
- **Exposure.** The scaler works in linear HDR and needs to know roughly how bright the image will be shown. Either enable `isAutoExposureEnabled` on the descriptor, or supply your own exposure texture.
- **Dynamic resolution.** Create the scaler for the largest input size and set `inputContentWidth` and `inputContentHeight` each frame to the region actually rendered.

## Exercises

- Add the spatial scaler to the render-target example: render at half size and compare with the `.linear` stretch.
- Visualize the motion texture while moving the camera.
- With the temporal scaler running, stop sending the jitter offset and describe what happens.
