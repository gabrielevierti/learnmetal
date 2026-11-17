# Model I/O

Nobody types the vertices of a character by hand. Artists build models in tools such as Blender and export them to files, and our job is to turn those files into vertex buffers, index buffers and textures.

On Apple platforms you do not need a third-party library for this. The system framework **Model I/O** reads common 3D formats, and **MetalKit** converts the result into Metal objects.

## Formats

Model I/O imports, among others:

| Format | Notes |
| --- | --- |
| USD, USDZ, USDA, USDC | Pixar's Universal Scene Description, Apple's preferred format. Supports materials, hierarchy and animation. |
| OBJ (+ MTL) | Simple and everywhere. Geometry and basic materials only. |
| PLY, STL | Geometry only, common for scans and 3D printing. |
| Alembic (ABC) | Baked animation caches. |

!!! note "What about glTF and FBX?"
    Model I/O does not read glTF or FBX. Convert them to USDZ with Apple's Reality Converter or with Blender, or use an open-source loader. For learning, OBJ and USDZ are plenty.

## How a model is structured

Model I/O represents a file as a tree:

- **`MDLAsset`**: the whole file. A container of objects.
- **`MDLObject`**: a node with a transform and children.
- **`MDLMesh`**: a node that has geometry. It owns vertex buffers and a vertex descriptor.
- **`MDLSubmesh`**: a part of a mesh drawn with one material. It owns an index buffer.
- **`MDLMaterial`**: named properties such as base color, roughness and normal, each a value or a texture.

One mesh shares its vertices among several submeshes. A car body might be one mesh with a submesh for paint, one for glass and one for chrome.

## Asking for the layout you want

Files store vertex data in whatever layout the exporter chose. Model I/O can rearrange it into the layout our shaders expect. Start from the Metal vertex descriptor, convert it, and name the attributes so Model I/O knows which data goes where:

```swift
import MetalKit
import ModelIO

let vertexDescriptor = MTLVertexDescriptor()
vertexDescriptor.attributes[0].format = .float3   // position
vertexDescriptor.attributes[0].offset = 0
vertexDescriptor.attributes[1].format = .float3   // normal
vertexDescriptor.attributes[1].offset = 12
vertexDescriptor.attributes[2].format = .float2   // uv
vertexDescriptor.attributes[2].offset = 24
vertexDescriptor.layouts[0].stride = 32

let mdlDescriptor = MTKModelIOVertexDescriptorFromMetal(vertexDescriptor)
(mdlDescriptor.attributes[0] as! MDLVertexAttribute).name = MDLVertexAttributePosition
(mdlDescriptor.attributes[1] as! MDLVertexAttribute).name = MDLVertexAttributeNormal
(mdlDescriptor.attributes[2] as! MDLVertexAttribute).name = MDLVertexAttributeTextureCoordinate
```

Since Model I/O writes the buffer for us, we are free to pack it tightly: `.float3` occupies 12 bytes in a vertex buffer, so a vertex is 32 bytes. This is the same vertex layout as our cube in spirit, only without Swift's padding. The shader's `VertexIn` does not change at all; `[[attribute(n)]]` hides the layout.

## Loading the asset

```swift
let allocator = MTKMeshBufferAllocator(device: device)
let url = Bundle.main.url(forResource: "backpack", withExtension: "usdz")!
let asset = MDLAsset(url: url,
                     vertexDescriptor: mdlDescriptor,
                     bufferAllocator: allocator)
```

The **buffer allocator** is the key detail. With an `MTKMeshBufferAllocator`, Model I/O loads vertex and index data straight into `MTLBuffer`s, with no intermediate copy.

Two optional steps are often useful right after loading:

```swift
asset.loadTextures()   // resolve texture references in materials

for case let mesh as MDLMesh in asset.childObjects(of: MDLMesh.self) {
    // Generate normals if the file has none.
    mesh.addNormals(withAttributeNamed: MDLVertexAttributeNormal, creaseThreshold: 0.5)
}
```

## From Model I/O to Metal

MetalKit turns every `MDLMesh` in the asset into an `MTKMesh`:

```swift
let (mdlMeshes, mtkMeshes) = try MTKMesh.newMeshes(asset: asset, device: device)
```

You get two parallel arrays. The `MTKMesh` objects hold the Metal buffers for drawing. The `MDLMesh` objects still hold what Metal does not care about: materials and transforms. The next two chapters wrap these into types of our own.

## Built-in shapes

Model I/O can also generate geometry, which is handy for tests:

```swift
let sphere = MDLMesh(sphereWithExtent: [1, 1, 1],
                     segments: [48, 48],
                     inwardNormals: false,
                     geometryType: .triangles,
                     allocator: allocator)
sphere.vertexDescriptor = mdlDescriptor
let sphereMesh = try MTKMesh(mesh: sphere, device: device)
```

There are similar initializers for boxes, planes, cylinders, capsules, cones and icosahedra.

!!! warning "Texture coordinates again"
    Many files follow the OpenGL convention with v pointing up. If a model's textures look scrambled or mirrored, flip v when loading: `mesh.flipTextureCoordinates(inAttributeNamed: MDLVertexAttributeTextureCoordinate)`.
