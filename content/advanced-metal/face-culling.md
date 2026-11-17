# Face Culling

Look at a closed object such as a cube from any angle, and you can see at most half of its faces. The faces pointing away from you are always hidden by the ones in front. **Face culling** tells the GPU to skip those triangles before rasterizing them, which saves roughly half of the fragment work for closed meshes.

## Winding order

How does the GPU know which side of a triangle is the front? By the order in which its three vertices appear on screen: clockwise or counter-clockwise. That order is the triangle's **winding**. When you turn a triangle around, its winding as seen from the camera flips.

```swift
let vertices: [Float] = [
    -0.5, -0.5, 0.0,   // 1
     0.5, -0.5, 0.0,   // 2
     0.0,  0.5, 0.0,   // 3   -> counter-clockwise when seen from +z
]
```

Models are exported with a consistent winding, so one setting works for a whole mesh.

## Enabling culling

Culling is render encoder state. It is not part of the pipeline state:

```swift
encoder.setFrontFacing(.counterClockwise)
encoder.setCullMode(.back)
```

| `MTLCullMode` | Effect |
| --- | --- |
| `.none` | Draw both sides. The default. |
| `.back` | Skip triangles facing away. |
| `.front` | Skip triangles facing the camera. |

!!! warning "Metal's default front face is clockwise"
    `MTLWinding.clockwise` is the default front-facing winding in Metal, the opposite of OpenGL. Our cube, and most model files, use counter-clockwise fronts, so always call `setFrontFacing(.counterClockwise)` together with `setCullMode`. If a model appears inside out, with only its far walls visible, this is the cause.

Encoder state resets with every new encoder, so set both at the start of each pass.

## When not to cull

- **Flat, two-sided geometry**: grass quads, leaves, cloth, windows. Disable culling for those draws with `setCullMode(.none)`.
- **Transparent closed objects**: you may want the inside faces visible through the outside ones. Draw the back faces first (`.front` culling), then the front faces.
- **Mirrored transforms**: a model matrix with a negative scale on one axis flips the winding of everything it draws. Flip the front-face setting for those objects.

## Culling front faces

Culling the *front* faces is occasionally useful on purpose. Rendering only back faces into a shadow map reduces a self-shadowing artifact, as you will see in [Shadow Mapping](../advanced-lighting/shadow-mapping.html), and a skybox cube seen from the inside can be drawn with front culling or simply with culling off.

## Which side am I on?

A fragment function can ask whether it belongs to a front-facing triangle, using a built-in input:

```cpp
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              bool isFrontFace [[front_facing]]) {
    float3 normal = normalize(in.normal);
    if (!isFrontFace) {
        normal = -normal;   // light the back side correctly
    }
    ...
}
```

This is how two-sided materials are lit correctly with culling turned off.

## Exercises

- Enable back-face culling and fly inside a cube.
- Reverse the winding of one cube face in the vertex data and observe which face disappears.
- Color front faces green and back faces red using `[[front_facing]]` with culling off.
