# Cubemaps

A **cubemap** is a texture made of six square images arranged as the faces of a cube. It is sampled with a 3D direction instead of a 2D coordinate: imagine standing at the center of the cube and looking along the direction, and you get the color that you see. Cubemaps are used for skies, reflections, and, later, for omnidirectional shadows and image-based lighting.

## Creating a cubemap

The six faces are stored as six **slices** of one texture of type `.typeCube`, in the order +X, -X, +Y, -Y, +Z, -Z (right, left, top, bottom, front, back).

**From six image files**, the shortest route is through Model I/O:

```swift
let names = ["right.jpg", "left.jpg", "top.jpg", "bottom.jpg", "front.jpg", "back.jpg"]
let mdlTexture = MDLTexture(cubeWithImagesNamed: names)!
let skybox = try loader.newTexture(texture: mdlTexture, options: [.SRGB: false])
```

**From one image** containing the six faces stacked top to bottom, the texture loader can split it:

```swift
let skybox = try loader.newTexture(URL: url, options: [
    .cubeLayout: MTKTextureLoader.CubeLayout.vertical,
    .SRGB: false,
])
```

**By hand**, when you generate or decode the faces yourself:

```swift
let descriptor = MTLTextureDescriptor.textureCubeDescriptor(pixelFormat: .rgba8Unorm,
                                                            size: 1024,
                                                            mipmapped: false)
let cube = device.makeTexture(descriptor: descriptor)!
for face in 0..<6 {
    cube.replace(region: MTLRegionMake2D(0, 0, 1024, 1024),
                 mipmapLevel: 0,
                 slice: face,
                 withBytes: facePixels[face],
                 bytesPerRow: 1024 * 4,
                 bytesPerImage: 1024 * 1024 * 4)
}
```

## A skybox

A skybox is a cube drawn around the camera and textured with a cubemap, giving the illusion of a vast environment. Its texture coordinate is simply the cube's local position, used as a direction.

```cpp
struct SkyOut {
    float4 position [[position]];
    float3 direction;
};

vertex SkyOut vertex_sky(VertexIn in [[stage_in]],
                         constant Uniforms &uniforms [[buffer(1)]]) {
    SkyOut out;
    float4 clip = uniforms.projection * uniforms.view * float4(in.position, 0.0);
    out.position = clip.xyww;
    out.direction = in.position;
    return out;
}

fragment float4 fragment_sky(SkyOut in [[stage_in]],
                             texturecube<float> sky [[texture(0)]],
                             sampler s [[sampler(0)]]) {
    return sky.sample(s, in.direction);
}
```

Two tricks are packed into the vertex function:

- The position is multiplied with **w = 0**, which removes the translation of the view matrix. The sky rotates with the camera but never gets closer.
- The output is `clip.xyww`. After the perspective divide, z becomes w / w = **1**, the far plane. The sky ends up behind everything.

Draw the sky **last**, after all opaque objects, with a depth state that uses `.lessEqual` and does not write depth:

```swift
let skyDepth = MTLDepthStencilDescriptor()
skyDepth.depthCompareFunction = .lessEqual
skyDepth.isDepthWriteEnabled = false
```

Drawn last, the sky's fragments are rejected wherever something else was drawn, so the sky costs only the pixels where it is visible. `.lessEqual` is needed because the sky's depth equals the cleared value of 1. The camera is inside the cube, so disable culling for this draw.

!!! note "Handedness"
    Cubemaps use a left-handed convention, a historical quirk shared by all graphics APIs. If a skybox looks mirrored in your right-handed world, negate the x or z component of the direction in the shader.

## Reflection

With the environment in a cubemap, a mirror-like surface is easy: reflect the view direction around the normal and use the result to sample the sky.

```cpp
fragment float4 fragment_reflect(VertexOut in [[stage_in]],
                                 constant FragmentUniforms &uniforms [[buffer(1)]],
                                 texturecube<float> sky [[texture(0)]],
                                 sampler s [[sampler(0)]]) {
    float3 incident = normalize(in.worldPosition - uniforms.viewPosition);
    float3 reflected = reflect(incident, normalize(in.normal));
    return sky.sample(s, reflected);
}
```

Combine it with a specular map to make only parts of a model reflective.

## Refraction

Light bends when it passes from one medium into another. `refract` computes the bent direction from the ratio of the two **refractive indices**:

| Material | Index |
| --- | --- |
| Air | 1.00 |
| Water | 1.33 |
| Glass | 1.52 |
| Diamond | 2.42 |

```cpp
float ratio = 1.00 / 1.52;   // from air into glass
float3 refracted = refract(incident, normalize(in.normal), ratio);
return sky.sample(s, refracted);
```

This is a single refraction at the surface. It is physically incomplete, but it looks convincingly glassy.

## Rendering into a cubemap

A static sky cannot reflect moving objects. For dynamic reflections, render the scene six times from the object's position, once into each face, with a 90 degree field of view and an aspect ratio of 1. Select the face with the attachment's `slice`:

```swift
pass.colorAttachments[0].texture = environmentCube
pass.colorAttachments[0].slice = face
```

Because of the cubemap convention, these six views must be built with a **left-handed** view and projection matrix, and the up vectors are fixed:

| Face | Look direction | Up |
| --- | --- | --- |
| +X | ( 1, 0, 0) | (0, 1, 0) |
| -X | (-1, 0, 0) | (0, 1, 0) |
| +Y | ( 0, 1, 0) | (0, 0, -1) |
| -Y | ( 0, -1, 0) | (0, 0, 1) |
| +Z | ( 0, 0, 1) | (0, 1, 0) |
| -Z | ( 0, 0, -1) | (0, 1, 0) |

```swift
extension float4x4 {
    init(lookAtLH eye: Float3, center: Float3, up: Float3) {
        let z = normalize(center - eye)
        let x = normalize(cross(up, z))
        let y = cross(z, x)
        self.init(columns: (
            SIMD4<Float>(x.x, y.x, z.x, 0),
            SIMD4<Float>(x.y, y.y, z.y, 0),
            SIMD4<Float>(x.z, y.z, z.z, 0),
            SIMD4<Float>(-dot(x, eye), -dot(y, eye), -dot(z, eye), 1)))
    }

    init(perspectiveLHFov fovY: Float, aspect: Float, near: Float, far: Float) {
        let y = 1 / tan(fovY * 0.5)
        let x = y / aspect
        let z = far / (far - near)
        self.init(columns: (
            SIMD4<Float>(x, 0, 0, 0),
            SIMD4<Float>(0, y, 0, 0),
            SIMD4<Float>(0, 0, z, 1),
            SIMD4<Float>(0, 0, -near * z, 0)))
    }
}
```

A left-handed view mirrors the scene, which reverses triangle winding, so use `setFrontFacing(.clockwise)` while rendering the faces. We reuse these helpers for [Point Shadows](../advanced-lighting/point-shadows.html) and for image-based lighting. Six scene renders per frame are expensive; engines update such probes rarely or one face per frame.

## Exercises

- Draw the skybox first instead of last, with depth writes off, and measure the difference in the Xcode GPU report on a heavy scene.
- Blend reflection and refraction by a factor that depends on the viewing angle.
