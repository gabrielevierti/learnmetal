# Mesh

MetalKit handed us `MTKMesh` objects. This chapter looks inside one, draws it, and wraps it together with its materials in a small type of our own.

## Inside an MTKMesh

| Property | Contents |
| --- | --- |
| `vertexBuffers` | An array of `MTKMeshBuffer`, each with a `buffer` (`MTLBuffer`) and an `offset` into it. |
| `vertexDescriptor` | The Model I/O vertex descriptor of the data. |
| `submeshes` | An array of `MTKSubmesh`. |
| `vertexCount` | Number of vertices. |

and each `MTKSubmesh` has:

| Property | Contents |
| --- | --- |
| `indexBuffer` | An `MTKMeshBuffer` with the indices. |
| `indexCount`, `indexType` | How many indices and whether they are 16 or 32 bit. |
| `primitiveType` | Usually `.triangle`. |

The offsets are important. The allocator may place several meshes in one large `MTLBuffer`, so always pass the offset when binding.

## Drawing a mesh

```swift
func draw(_ mesh: MTKMesh, with encoder: MTLRenderCommandEncoder) {
    for (index, vertexBuffer) in mesh.vertexBuffers.enumerated() {
        encoder.setVertexBuffer(vertexBuffer.buffer, offset: vertexBuffer.offset, index: index)
    }
    for submesh in mesh.submeshes {
        encoder.drawIndexedPrimitives(type: submesh.primitiveType,
                                      indexCount: submesh.indexCount,
                                      indexType: submesh.indexType,
                                      indexBuffer: submesh.indexBuffer.buffer,
                                      indexBufferOffset: submesh.indexBuffer.offset)
    }
}
```

With the layout from the previous chapter there is one vertex buffer, bound at slot 0, which leaves slot 1 for uniforms as before.

The pipeline state needs the matching Metal vertex descriptor. Either reuse the one you built by hand or derive it from the mesh:

```swift
pipelineDescriptor.vertexDescriptor = MTKMetalVertexDescriptorFromModelIO(mesh.vertexDescriptor)
```

## Materials

Each `MDLSubmesh` has an optional `MDLMaterial`. A material is a bag of properties looked up by **semantic**:

```swift
let property = mdlSubmesh.material?.property(with: .baseColor)
```

A property can be a plain value or a texture, so we handle both. A small material type for the Phong shader from the lighting section:

```swift
struct MeshMaterial {
    var baseColor = Float3(1, 1, 1)
    var baseColorTexture: MTLTexture?
    var specularTexture: MTLTexture?
    var shininess: Float = 32
}

extension MeshMaterial {
    init(_ material: MDLMaterial?, loader: MTKTextureLoader) {
        guard let material else { return }

        if let property = material.property(with: .baseColor) {
            if property.type == .float3 {
                baseColor = property.float3Value
            }
            baseColorTexture = Self.texture(for: property, loader: loader, sRGB: true)
        }
        if let property = material.property(with: .specular) {
            specularTexture = Self.texture(for: property, loader: loader, sRGB: false)
        }
    }

    private static func texture(for property: MDLMaterialProperty,
                                loader: MTKTextureLoader,
                                sRGB: Bool) -> MTLTexture? {
        let options: [MTKTextureLoader.Option: Any] = [
            .generateMipmaps: true,
            .SRGB: sRGB,
        ]
        switch property.type {
        case .texture:
            guard let mdlTexture = property.textureSamplerValue?.texture else { return nil }
            return try? loader.newTexture(texture: mdlTexture, options: options)
        case .URL:
            guard let url = property.urlValue else { return nil }
            return try? loader.newTexture(URL: url, options: options)
        default:
            return nil
        }
    }
}
```

The texture case covers images embedded in USDZ archives (after `asset.loadTextures()`), and the URL case covers OBJ files that reference images on disk next to the `.mtl` file.

!!! note "The sRGB flag"
    Color textures are stored in sRGB, data textures such as specular or normal maps are not. Until the [Gamma Correction](../advanced-lighting/gamma-correction.html) chapter, pass `false` for everything so the output matches earlier chapters.

## A Mesh type

Bundle the Metal mesh with one material per submesh:

```swift
struct Mesh {
    let mtkMesh: MTKMesh
    let materials: [MeshMaterial]

    init(mdlMesh: MDLMesh, mtkMesh: MTKMesh, loader: MTKTextureLoader) {
        self.mtkMesh = mtkMesh
        let submeshes = mdlMesh.submeshes as? [MDLSubmesh] ?? []
        self.materials = submeshes.map { MeshMaterial($0.material, loader: loader) }
    }

    func draw(with encoder: MTLRenderCommandEncoder, fallback: MTLTexture) {
        for (index, vertexBuffer) in mtkMesh.vertexBuffers.enumerated() {
            encoder.setVertexBuffer(vertexBuffer.buffer, offset: vertexBuffer.offset, index: index)
        }
        for (submesh, material) in zip(mtkMesh.submeshes, materials) {
            encoder.setFragmentTexture(material.baseColorTexture ?? fallback, index: 0)
            encoder.setFragmentTexture(material.specularTexture ?? fallback, index: 1)
            encoder.drawIndexedPrimitives(type: submesh.primitiveType,
                                          indexCount: submesh.indexCount,
                                          indexType: submesh.indexType,
                                          indexBuffer: submesh.indexBuffer.buffer,
                                          indexBufferOffset: submesh.indexBuffer.offset)
        }
    }
}
```

## A fallback texture

A shader that samples a texture must have one bound. For materials without a texture, bind a 1×1 white texture, which multiplies to nothing:

```swift
func makeSolidTexture(device: MTLDevice, color: SIMD4<UInt8>) -> MTLTexture {
    let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm,
                                                              width: 1, height: 1,
                                                              mipmapped: false)
    let texture = device.makeTexture(descriptor: descriptor)!
    var pixel = color
    texture.replace(region: MTLRegionMake2D(0, 0, 1, 1),
                    mipmapLevel: 0,
                    withBytes: &pixel,
                    bytesPerRow: 4)
    return texture
}
```

This is also your first hand-made texture: a descriptor, `makeTexture`, and `replace` to upload bytes.
