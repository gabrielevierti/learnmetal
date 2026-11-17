# Shadow Mapping

Shadows anchor objects to the ground and reveal how things are arranged in space. The standard real-time technique is **shadow mapping**, and it is built from parts you already know: a depth buffer and render-to-texture.

## The idea

A point is in shadow if something sits between it and the light. Put a camera at the light and render the scene's **depth** into a texture. That texture, the **shadow map**, records for every direction how far the light reaches before hitting something.

When shading a fragment in the main pass, transform it into the light's view and compare its depth with the shadow map. If the fragment is farther from the light than the stored value, something closer is blocking the light.

## The shadow map texture

```swift
let shadowSize = 2048
let descriptor = MTLTextureDescriptor.texture2DDescriptor(
    pixelFormat: .depth32Float, width: shadowSize, height: shadowSize, mipmapped: false)
descriptor.usage = [.renderTarget, .shaderRead]
descriptor.storageMode = .private
shadowMap = device.makeTexture(descriptor: descriptor)!

shadowPass = MTLRenderPassDescriptor()
shadowPass.depthAttachment.texture = shadowMap
shadowPass.depthAttachment.loadAction = .clear
shadowPass.depthAttachment.clearDepth = 1.0
shadowPass.depthAttachment.storeAction = .store
```

The pass has **no color attachment** at all. This time the depth must be stored, since reading it is the whole point.

## The light's matrices

A directional light has parallel rays, so its projection is **orthographic**: a box with no perspective. Add to `Math.swift`:

```swift
extension float4x4 {
    /// Right-handed orthographic projection with a 0...1 depth range.
    init(orthographicLeft l: Float, right r: Float, bottom b: Float, top t: Float,
         near n: Float, far f: Float) {
        self.init(columns: (
            SIMD4<Float>(2 / (r - l), 0, 0, 0),
            SIMD4<Float>(0, 2 / (t - b), 0, 0),
            SIMD4<Float>(0, 0, 1 / (n - f), 0),
            SIMD4<Float>((l + r) / (l - r), (t + b) / (b - t), n / (n - f), 1)))
    }
}
```

```swift
let lightPosition = Float3(-2, 4, -1)
let lightView = float4x4(lookAt: lightPosition, center: [0, 0, 0], up: [0, 1, 0])
let lightProjection = float4x4(orthographicLeft: -10, right: 10, bottom: -10, top: 10,
                               near: 1, far: 12)
let lightViewProjection = lightProjection * lightView
```

The box must contain everything that casts or receives shadows in the area you care about. Keep it as tight as you can: the shadow map's resolution is spread over the box.

## The depth pass

The pipeline for this pass has a vertex function, no fragment function, and no color format:

```cpp
vertex float4 vertex_shadow(VertexIn in [[stage_in]],
                            constant ShadowUniforms &uniforms [[buffer(1)]]) {
    return uniforms.lightViewProjection * uniforms.model * float4(in.position, 1.0);
}
```

```swift
let descriptor = MTLRenderPipelineDescriptor()
descriptor.vertexFunction = library.makeFunction(name: "vertex_shadow")
descriptor.fragmentFunction = nil
descriptor.vertexDescriptor = vertexDescriptor
descriptor.depthAttachmentPixelFormat = .depth32Float
shadowPipelineState = try device.makeRenderPipelineState(descriptor: descriptor)
```

A vertex function may return a bare `float4`; it is taken as the position. Each frame, render the scene with this pipeline into `shadowPass` before the main pass, using the same command buffer.

## Using the shadow map

In the main pass, the vertex function also outputs the position in the light's clip space:

```cpp
out.shadowPosition = uniforms.lightViewProjection * world;
```

The fragment function converts that to a texture coordinate and a depth to compare:

```cpp
static float calcShadow(float4 shadowPosition, depth2d<float> shadowMap, sampler shadowSampler) {
    float3 proj = shadowPosition.xyz / shadowPosition.w;
    float2 uv = proj.xy * float2(0.5, -0.5) + 0.5;

    if (proj.z > 1.0) {
        return 1.0;    // beyond the light's far plane: lit
    }
    return shadowMap.sample_compare(shadowSampler, uv, proj.z);
}
```

- Dividing by w is unnecessary for an orthographic projection but makes the function work for perspective lights as well.
- NDC x and y run from -1 to 1 with y up, and texture coordinates run from 0 to 1 with y down. Hence the scale of `(0.5, -0.5)`. Depth is already in the 0 to 1 range and needs no conversion.
- Depth textures have their own shader type, `depth2d<float>`.

`sample_compare` compares the reference depth against the texture and returns 1 if the test passes and 0 if not. The test is configured on the sampler:

```swift
let shadowSamplerDescriptor = MTLSamplerDescriptor()
shadowSamplerDescriptor.minFilter = .linear
shadowSamplerDescriptor.magFilter = .linear
shadowSamplerDescriptor.compareFunction = .lessEqual
shadowSamplerDescriptor.sAddressMode = .clampToEdge
shadowSamplerDescriptor.tAddressMode = .clampToEdge
shadowSampler = device.makeSamplerState(descriptor: shadowSamplerDescriptor)!
```

With `.lessEqual`, the result is 1 where the fragment is at or in front of the stored depth, meaning lit. Apply it to the diffuse and specular terms and leave ambient alone:

```cpp
float lit = calcShadow(in.shadowPosition, shadowMap, shadowSampler);
float3 color = ambient + lit * (diffuse + specular);
```

## Shadow acne

The first result is covered in dark stripes. The shadow map has limited resolution, so many fragments share one texel, and across a slanted surface half of them come out slightly behind the stored depth. This is **shadow acne**.

The cure is a **depth bias**: push the stored depth a little away from the light. Metal applies it during rasterization of the shadow pass:

```swift
shadowEncoder.setDepthBias(0.015, slopeScale: 7, clamp: 0.02)
```

The constant part is measured in units that depend on the depth format, so treat these numbers as a starting point. The slope-scaled part automatically increases the bias on surfaces at a steep angle to the light, which need it most. Too much bias detaches the shadow from its caster, an artifact known as **peter panning**. Tune until both disappear. Rendering only back faces into the shadow map (`setCullMode(.front)`) also helps for closed meshes.

## Softer edges

Because the comparison sampler uses linear filtering, the GPU compares the four nearest texels and blends the *results*. That is hardware **percentage-closer filtering** (PCF), and it softens edges for free. Averaging a few more taps softens them further:

```cpp
float2 texel = 1.0 / float2(shadowMap.get_width(), shadowMap.get_height());
float lit = 0.0;
for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++) {
        lit += shadowMap.sample_compare(shadowSampler, uv + float2(x, y) * texel, proj.z);
    }
}
lit /= 9.0;
```

## Outside the map

Fragments outside the light's box sample beyond the texture. With `.clampToEdge` they repeat the border texel, which can smear shadows across the scene. Either return "lit" when `uv` is outside 0 to 1, or use `.clampToBorderColor` with an opaque white border where it is supported.

## Beyond one map

A single map cannot cover a large outdoor scene with enough resolution. **Cascaded shadow maps** split the view frustum into several ranges, each with its own map, stored in the layers of a `depth2d_array` texture. For spotlights, use a perspective projection for the light and the same code.

## Exercises

- Display the shadow map on a full-screen triangle to check what the light sees.
- Set the bias to zero, then to a large value, and identify acne and peter panning.
- Move the light over time and watch the shadows follow.
