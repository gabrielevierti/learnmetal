# Tile-Based GPUs

Every Apple GPU, from the iPhone to the Mac Studio, is a **tile-based deferred renderer** (TBDR). It draws a frame in a different order than the immediate-mode desktop GPUs most tutorials assume, and several Metal features exist only because of that. Knowing how it works turns a list of odd-looking rules into common sense.

## How a tile-based GPU draws a pass

An immediate-mode GPU takes each triangle as it arrives and shades it straight into the framebuffer in memory. An Apple GPU works in two phases per render pass.

1. **Tiling.** It runs the vertex functions of every draw call in the pass, splits the screen into small tiles (for example 32 × 32 pixels), and records which triangles touch each tile.
2. **Rendering.** For each tile it loads the tile's pixels into a small, very fast memory inside the GPU, the **tile memory**; finds which triangle is visible at each pixel; shades only those; and writes the finished tile back to the texture.

Two consequences follow, and they explain the rest of this chapter.

- **Hidden surface removal.** For opaque geometry the GPU knows the visible triangle of each pixel before it runs any fragment function. Hidden fragments cost nothing, whatever the draw order.
- **Reading and writing textures is the expensive part.** Work inside tile memory is cheap. Moving a tile between tile memory and system memory costs bandwidth, power and time.

!!! note "Coming from OpenGL"
    On a desktop GPU you sort opaque objects front to back to save fragment work. On Apple GPUs hidden surface removal does that for you, as long as the pipeline is opaque. What you manage instead is passes: how many there are, and what each one loads and stores.

## Load and store actions

Each attachment of a pass has a load action, applied when a tile starts, and a store action, applied when it ends.

- `.load` copies the old contents from memory into every tile. Use it only when you draw on top of an earlier result.
- `.clear` fills the tile with a value, with no memory traffic. `.dontCare` does nothing at all.
- `.store` writes the tile back. `.dontCare` discards it.

The rule: **load only what you need to keep, store only what you will read later.** A depth texture used by a single pass should be `.clear` and `.dontCare`. A multisampled color texture should be `.multisampleResolve`, without storing the samples.

```swift
let pass = MTLRenderPassDescriptor()
pass.colorAttachments[0].texture = drawable.texture
pass.colorAttachments[0].loadAction = .clear          // every pixel gets drawn: nothing to load
pass.colorAttachments[0].storeAction = .store         // the image is what we want
pass.depthAttachment.texture = depthTexture
pass.depthAttachment.loadAction = .clear
pass.depthAttachment.storeAction = .dontCare          // nobody reads the depth after this pass
```

## Memoryless textures

If an attachment is never loaded and never stored, it only ever lives in tile memory, so it does not need memory of its own. Give it the **memoryless** storage mode and Metal allocates nothing for it. At 4K, a depth texture and a 4× multisampled color texture add up to hundreds of megabytes saved.

```swift
let descriptor = MTLTextureDescriptor.texture2DDescriptor(
    pixelFormat: .depth32Float, width: width, height: height, mipmapped: false)
descriptor.usage = .renderTarget
descriptor.storageMode = .memoryless                  // exists only in tile memory
let depthTexture = device.makeTexture(descriptor: descriptor)!
```

With MetalKit, `MTKView` already does this for its own depth and multisample textures on Apple silicon.

## Do more in one pass

Starting a new pass means storing the tiles of the old one and loading them again. The deferred renderer of the [Deferred Shading](../advanced-lighting/deferred-shading.html) chapter does exactly that: one pass stores three G-buffer textures, a second pass samples them. On a tile-based GPU both steps can run in **one** pass, with the G-buffer never leaving tile memory.

The tool is **programmable blending**: a fragment function may read the current value of the color attachments it is drawing to, by taking them as parameters.

```cpp
struct LightingOut {
    float4 lit [[color(0)]];
};

// Drawn after the geometry, in the same render pass.
fragment LightingOut fragment_lighting(ScreenOut in [[stage_in]],
                                       float4 albedo   [[color(1)]],
                                       float4 normal   [[color(2)]],
                                       float  depth    [[color(3)]],
                                       constant LightingUniforms &uniforms [[buffer(0)]]) {
    // albedo, normal and depth are this pixel's G-buffer values, read from tile memory.
    LightingOut out;
    out.lit = float4(shade(albedo.rgb, normal.xyz, depth, in.uv, uniforms), 1.0);
    return out;
}
```

The G-buffer attachments become memoryless, with `.clear` and `.dontCare`; only the lit color is stored. The depth is written to an extra `r32Float` color attachment, because the depth attachment itself cannot be read this way. The cost of deferred shading drops to little more than that of forward rendering, which is why this pattern is the standard on iPhone.

Programmable blending also gives you custom blend equations and order-independent transparency. For per-pixel data that does not fit a pixel format, **image blocks** and **tile shaders** let you define your own layout of tile memory and run a compute-like function on each tile in the middle of a render pass.

## Keep hidden surface removal working

Hidden surface removal can only skip fragments it knows to be covered by opaque ones. Three things defeat it.

- **Blending.** A blended fragment needs what is behind it.
- **`discard_fragment`** and alpha testing: the GPU cannot know the pixel is covered until the function has run.
- **Writing depth from the fragment function**, or reading the attachment with programmable blending.

So draw in this order: **opaque** first, then **alpha-tested**, then **translucent**. Sorting opaque objects is not needed. Keep `discard_fragment` out of shaders that do not need it, since its presence alone, even if never executed, moves the draw out of the opaque group.

## Other habits that matter

- **Do not split a pass.** Ending an encoder and starting another with the same attachments forces a store and a load. Encode everything that targets the same textures in one encoder.
- **Avoid reading your own render target** with a texture sample in the same frame when programmable blending would do.
- **Compress textures** with ASTC and generate mipmaps; bandwidth, not arithmetic, is usually the limit on mobile.
- **Use smaller formats.** `rgba16Float` costs twice the bandwidth of `rg11b10Float` and is rarely needed for HDR color.
- **Use half precision** (`half`, `half3`) in fragment functions for colors and normals. On Apple GPUs it is faster and uses fewer registers.
- **Measure.** The Metal debugger in Xcode shows the load and store actions of every pass, and the memory report flags textures that could be memoryless. Metal System Trace in Instruments shows the tiling and rendering time of each pass separately.

## Exercises

- Find a depth texture in one of your renderers that could be memoryless, and change it.
- Set the store action of the color attachment to `.dontCare` and explain what you see.
- Add an unused `discard_fragment` behind an always-false uniform condition and compare the fragment time of a scene with heavy overdraw.
