# Model

A file usually contains several meshes arranged in a hierarchy, each with its own transform. A `Model` type collects them so that loading and drawing a whole file is one line each.

<!-- cpp -->

!!! note "Model loading in C++"
    Model I/O and MetalKit's mesh types are not part of metal-cpp. The C++ version of this section loads Wavefront OBJ files with the single-header library [tinyobjloader](https://github.com/tinyobjloader/tinyobjloader) and builds the Metal buffers by hand. The ideas are the same: a model is meshes, a mesh has one vertex buffer and one index buffer per material, and a material is values plus textures. To load USD from C++, call Model I/O from a small Objective-C++ file, as the window code in [Project Setup](../getting-started/project-setup.html) does for AppKit, or convert the model to OBJ or glTF.

<!-- /cpp -->

## The Model class

```swift
import MetalKit
import ModelIO

final class Model {
    struct Node {
        let mesh: Mesh
        let transform: float4x4   // mesh space to model space
    }

    let nodes: [Node]

    init(url: URL,
         device: MTLDevice,
         vertexDescriptor: MDLVertexDescriptor,
         loader: MTKTextureLoader) throws {
        let allocator = MTKMeshBufferAllocator(device: device)
        let asset = MDLAsset(url: url,
                             vertexDescriptor: vertexDescriptor,
                             bufferAllocator: allocator)
        asset.loadTextures()

        let (mdlMeshes, mtkMeshes) = try MTKMesh.newMeshes(asset: asset, device: device)

        nodes = zip(mdlMeshes, mtkMeshes).map { mdlMesh, mtkMesh in
            Node(mesh: Mesh(mdlMesh: mdlMesh, mtkMesh: mtkMesh, loader: loader),
                 transform: Model.worldTransform(of: mdlMesh))
        }
    }

    /// Multiplies the local transforms from the mesh up to the root.
    private static func worldTransform(of object: MDLObject) -> float4x4 {
        var transform = float4x4.identity
        var current: MDLObject? = object
        while let node = current {
            if let local = node.transform {
                transform = local.matrix * transform
            }
            current = node.parent
        }
        return transform
    }
}
```

Every `MDLObject` can carry a transform relative to its parent. Walking up the parent chain and multiplying gives the mesh's placement within the model. Simple OBJ files have no hierarchy, so the loop just returns the identity. USD files often do, and skipping this step is why parts of a model sometimes appear piled up at the origin.

## Drawing

Each node combines the model's own matrix with its node transform:

```swift
extension Model {
    func draw(with encoder: MTLRenderCommandEncoder,
              modelMatrix: float4x4,
              uniforms: inout Uniforms,
              fallback: MTLTexture) {
        for node in nodes {
            uniforms.model = modelMatrix * node.transform
            uniforms.normalMatrix = uniforms.model.upperLeft.inverse.transpose
            encoder.setVertexBytes(&uniforms, length: MemoryLayout<Uniforms>.stride, index: 1)
            node.mesh.draw(with: encoder, fallback: fallback)
        }
    }
}
```

In the renderer:

```swift
// init
let url = Bundle.main.url(forResource: "backpack", withExtension: "usdz")!
model = try! Model(url: url, device: device, vertexDescriptor: mdlDescriptor, loader: loader)

// draw(in:)
encoder.setRenderPipelineState(pipelineState)
encoder.setDepthStencilState(depthState)
encoder.setFragmentBytes(&fragmentUniforms, length: MemoryLayout<FragmentUniforms>.stride, index: 1)
encoder.setFragmentSamplerState(samplerState, index: 0)
model.draw(with: encoder,
           modelMatrix: float4x4(rotation: time * 0.5, axis: [0, 1, 0]),
           uniforms: &uniforms,
           fallback: whiteTexture)
```

Add the point lights from the previous section and you have a properly lit, textured model.

## Finding models

- Apple publishes sample USDZ models in its AR Quick Look gallery.
- Sites such as Sketchfab, Poly Haven and Kenney offer free models. Check each license.
- Blender exports both OBJ and USD.

When a model looks wrong, the usual suspects are, in order: flipped texture coordinates, missing normals, a scale that is off by a factor of 100 (centimeters versus meters), and ignored node transforms.

## Bounds and framing

An unknown model can be any size. Model I/O reports the bounding box, which lets you scale and center anything automatically:

```swift
let bounds = asset.boundingBox
let size = bounds.maxBounds - bounds.minBounds
let center = (bounds.maxBounds + bounds.minBounds) * 0.5
let scale = 2.0 / max(size.x, max(size.y, size.z))

let normalize = float4x4(scale: Float3(repeating: scale)) * float4x4(translation: -center)
```

Multiply `normalize` into the model matrix and every model fits in a box two units wide around the origin.

## What we left out

A production loader also handles skeletal animation (`MDLSkeleton`, `MDLAnimationBindComponent`), morph targets, cameras and lights stored in the file, and it caches textures so an image shared by ten materials is loaded once. Add a dictionary from URL to `MTLTexture` to the material loader as a first improvement.

## Exercises

- Draw the model ten times using the cube positions from the first section.
- Implement the texture cache.
- Load a model with no textures and confirm that the fallback texture and `baseColor` produce a sensible result. You will need to pass `baseColor` to the shader in the fragment uniforms.
