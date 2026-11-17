# Stencil Testing

Next to the depth buffer lives the **stencil buffer**: 8 bits per pixel that you can write freely while drawing and test against later. It lets you mark regions of the screen and then restrict drawing to them. Outlines, portals, mirrors and masking UI are classic uses.

## Enabling a stencil buffer

Depth and stencil normally share one texture with a combined format:

```swift
view.depthStencilPixelFormat = .depth32Float_stencil8
view.clearStencil = 0

pipelineDescriptor.depthAttachmentPixelFormat = .depth32Float_stencil8
pipelineDescriptor.stencilAttachmentPixelFormat = .depth32Float_stencil8
```

Every pipeline state used in the pass must declare both formats.

## The stencil test

For each fragment the GPU compares a **reference value**, which you set on the encoder, with the value in the buffer. The comparison and the reaction are described by an `MTLStencilDescriptor` inside the depth-stencil descriptor:

| Property | Meaning |
| --- | --- |
| `stencilCompareFunction` | How reference and stored value are compared. |
| `stencilFailureOperation` | What to do with the stored value if the stencil test fails. |
| `depthFailureOperation` | If the stencil test passes but the depth test fails. |
| `depthStencilPassOperation` | If both pass. |
| `readMask`, `writeMask` | Bit masks applied when comparing and when writing. |

The operations are `.keep`, `.zero`, `.replace` (store the reference value), `.incrementClamp`, `.decrementClamp`, `.invert`, `.incrementWrap` and `.decrementWrap`.

There are separate descriptors for front-facing and back-facing triangles, `frontFaceStencil` and `backFaceStencil`.

## Object outlines

A selection outline is drawn in two steps:

1. Draw the object normally and write 1 into the stencil buffer wherever it is visible.
2. Draw the object again, slightly enlarged and in a flat color, only where the stencil is **not** 1.

The enlarged copy is rejected over the object itself, and survives only in a thin border around it.

**State 1: write 1 wherever the object is drawn.**

```swift
let writeStencil = MTLStencilDescriptor()
writeStencil.stencilCompareFunction = .always
writeStencil.depthStencilPassOperation = .replace

let writeDescriptor = MTLDepthStencilDescriptor()
writeDescriptor.depthCompareFunction = .less
writeDescriptor.isDepthWriteEnabled = true
writeDescriptor.frontFaceStencil = writeStencil
writeDescriptor.backFaceStencil = writeStencil
let writeState = device.makeDepthStencilState(descriptor: writeDescriptor)!
```

**State 2: draw only where the stencil is not 1, ignoring depth.**

```swift
let testStencil = MTLStencilDescriptor()
testStencil.stencilCompareFunction = .notEqual
testStencil.depthStencilPassOperation = .keep

let outlineDescriptor = MTLDepthStencilDescriptor()
outlineDescriptor.depthCompareFunction = .always
outlineDescriptor.isDepthWriteEnabled = false
outlineDescriptor.frontFaceStencil = testStencil
outlineDescriptor.backFaceStencil = testStencil
let outlineState = device.makeDepthStencilState(descriptor: outlineDescriptor)!
```

**Drawing:**

```swift
// Floor and anything else that should not be outlined: the ordinary depth state.
encoder.setDepthStencilState(depthState)
drawFloor(encoder)

// 1. The cubes, marking the stencil buffer.
encoder.setDepthStencilState(writeState)
encoder.setStencilReferenceValue(1)
encoder.setRenderPipelineState(pipelineState)
drawCubes(encoder, scale: 1.0)

// 2. The outlines.
encoder.setDepthStencilState(outlineState)
encoder.setRenderPipelineState(solidColorPipelineState)
drawCubes(encoder, scale: 1.05)
```

The `solidColorPipelineState` uses a fragment function that returns a single color. Because the outline state uses `.always` for depth, the border shows through other objects, which is what you want for a selection highlight.

!!! note "Better outlines"
    Scaling works for convex shapes centered on their origin. For arbitrary models, move each vertex along its normal in the vertex function instead: `position + normal * thickness`.

## Reading the comparison correctly

The comparison is written as *reference* **op** *stored*. With `.less` and a reference of 1, a fragment passes where `1 < stored`. It is easy to read this backwards.

## Other uses

- **Portals and mirrors**: draw the portal shape into the stencil buffer, then draw the world seen through it only where the stencil is set.
- **Masking**: clip UI or 2D content to arbitrary shapes.
- **Deferred lighting volumes**: mark the pixels a light can reach so the lighting shader runs only there.

## Exercises

- Make the outline respect depth, so it is hidden behind closer objects.
- Outline only one of the cubes.
