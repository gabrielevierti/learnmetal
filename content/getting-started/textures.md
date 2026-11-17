# Textures

Giving every vertex a color cannot produce a brick wall or a wooden crate. For detail we wrap images around geometry. An image used this way is a **texture**, and reading a color from it is called **sampling**.

## Texture coordinates

Each vertex gets a 2D **texture coordinate** (often called UV) that says which point of the image belongs to it. Coordinates run from 0 to 1 on both axes, and they are interpolated across the triangle like any other vertex output.

!!! warning "Metal's origin is at the top left"
    In Metal, texture coordinate (0, 0) is the **top-left** corner of the image and v increases downward. OpenGL puts (0, 0) at the bottom left. Texture coordinates copied from OpenGL tutorials or exported by tools that follow the OpenGL convention will show images upside down unless you flip v (`v = 1 - v`) or flip the image when loading.

A rectangle with positions and texture coordinates:

```swift
let vertices: [Float] = [
    // position          // uv
     0.5,  0.5, 0.0,     1.0, 0.0,   // top right
     0.5, -0.5, 0.0,     1.0, 1.0,   // bottom right
    -0.5, -0.5, 0.0,     0.0, 1.0,   // bottom left
    -0.5,  0.5, 0.0,     0.0, 0.0,   // top left
]
```

```swift
let floatSize = MemoryLayout<Float>.stride
vertexDescriptor.attributes[0].format = .float3
vertexDescriptor.attributes[0].offset = 0
vertexDescriptor.attributes[0].bufferIndex = 0
vertexDescriptor.attributes[1].format = .float2
vertexDescriptor.attributes[1].offset = floatSize * 3
vertexDescriptor.attributes[1].bufferIndex = 0
vertexDescriptor.layouts[0].stride = floatSize * 5
```

## Loading an image

MetalKit's `MTKTextureLoader` decodes PNG, JPEG, HEIC, TIFF and other common formats and uploads the result to a new `MTLTexture`. Drag an image such as `container.jpg` into the project, then:

```swift
let texture: MTLTexture

// in init
let loader = MTKTextureLoader(device: device)
let url = Bundle.main.url(forResource: "container", withExtension: "jpg")!
let options: [MTKTextureLoader.Option: Any] = [
    .generateMipmaps: true,
    .SRGB: false,
]
texture = try! loader.newTexture(URL: url, options: options)
```

`.SRGB: false` tells the loader to treat pixel values as plain numbers. We will revisit that choice in [Gamma Correction](../advanced-lighting/gamma-correction.html). If you ever need the OpenGL orientation, add `.origin: MTKTextureLoader.Origin.bottomLeft`, which flips the image vertically during loading.

Images in an asset catalog can be loaded by name with `loader.newTexture(name:scaleFactor:bundle:options:)`.

## Samplers

A texture is only pixels. How they are read is decided by a separate object, the **sampler state**:

```swift
let samplerState: MTLSamplerState

// in init
let samplerDescriptor = MTLSamplerDescriptor()
samplerDescriptor.minFilter = .linear
samplerDescriptor.magFilter = .linear
samplerDescriptor.mipFilter = .linear
samplerDescriptor.sAddressMode = .repeat
samplerDescriptor.tAddressMode = .repeat
samplerState = device.makeSamplerState(descriptor: samplerDescriptor)!
```

**Address modes** decide what happens outside the 0 to 1 range:

| Mode | Effect |
| --- | --- |
| `.clampToEdge` | The edge pixels stretch outward. This is the default. |
| `.repeat` | The image tiles. |
| `.mirrorRepeat` | The image tiles, mirrored each time. |
| `.clampToBorderColor` | Outside is a fixed border color (macOS and newer iOS devices). |
| `.clampToZero` | Outside is transparent black. |

**Filtering** decides what happens when a texture pixel (a *texel*) does not map one to one onto a screen pixel. `.nearest` picks the closest texel and looks blocky when magnified. `.linear` blends the four nearest texels and looks smooth.

**Mipmaps** are a chain of pre-shrunk copies of the texture, each half the size of the previous one. When a surface is far away, sampling a small copy avoids shimmering and is faster. `mipFilter = .linear` blends between the two closest levels, which together with linear min filtering is known as trilinear filtering. Setting `samplerDescriptor.maxAnisotropy = 8` further sharpens surfaces seen at a steep angle.

!!! note "Coming from OpenGL"
    Wrap and filter settings are not properties of the texture. One texture can be read through several samplers, and one sampler can serve every texture.

## Sampling in the shader

```cpp
struct VertexIn {
    float3 position [[attribute(0)]];
    float2 uv       [[attribute(1)]];
};

struct VertexOut {
    float4 position [[position]];
    float2 uv;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]]) {
    VertexOut out;
    out.position = float4(in.position, 1.0);
    out.uv = in.uv;
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              texture2d<float> colorTexture [[texture(0)]],
                              sampler textureSampler [[sampler(0)]]) {
    return colorTexture.sample(textureSampler, in.uv);
}
```

Textures and samplers have their own index tables, selected with `[[texture(n)]]` and `[[sampler(n)]]`. Bind them before drawing:

```swift
encoder.setFragmentTexture(texture, index: 0)
encoder.setFragmentSamplerState(samplerState, index: 0)
```

Run it and the rectangle shows your image.

## Two textures at once

A fragment function can read many textures. Load a second image, bind it at index 1, and blend:

```cpp
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              texture2d<float> texture0 [[texture(0)]],
                              texture2d<float> texture1 [[texture(1)]],
                              sampler textureSampler [[sampler(0)]]) {
    float4 a = texture0.sample(textureSampler, in.uv);
    float4 b = texture1.sample(textureSampler, in.uv);
    return mix(a, b, 0.2);
}
```

`mix(a, b, t)` returns `a * (1 - t) + b * t`, so the result is 80% of the first texture and 20% of the second.

## Exercises

- Multiply the uv by 2 in the fragment function and try each address mode.
- Switch the filters to `.nearest` and display only the center of the texture (uv from 0.45 to 0.55) to see individual texels.
- Add a uniform that controls the `mix` factor and animate it.
