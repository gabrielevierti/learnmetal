```cpp
struct Submesh {
    MTL::Buffer* indexBuffer;
    NS::UInteger indexCount;
    int materialIndex;
};

void draw(MTL::Buffer* vertexBuffer, const std::vector<Submesh>& submeshes, MTL::RenderCommandEncoder* encoder) {
    encoder->setVertexBuffer(vertexBuffer, 0, 0);
    for (const Submesh& submesh : submeshes) {
        encoder->drawIndexedPrimitives(MTL::PrimitiveTypeTriangle,
                                       submesh.indexCount,
                                       MTL::IndexTypeUInt32,
                                       submesh.indexBuffer,
                                       0);
    }
}
```

```cpp
// The vertex descriptor is the one we built by hand in the previous chapter.
pipelineDescriptor->setVertexDescriptor(vertexDescriptor);
```

```cpp
// tinyobj stores one material index per face; we use the first face's material for the shape.
const tinyobj::material_t& material = materials[shape.mesh.material_ids[0]];
```

```cpp
struct MeshMaterial {
    simd::float3 baseColor = {1, 1, 1};
    MTL::Texture* baseColorTexture = nullptr;
    MTL::Texture* specularTexture = nullptr;
    float shininess = 32;
};

MeshMaterial makeMaterial(const tinyobj::material_t& material, const std::string& directory,
                          MTL::Device* device, MTL::CommandQueue* queue) {
    MeshMaterial result;
    result.baseColor = {material.diffuse[0], material.diffuse[1], material.diffuse[2]};
    result.shininess = material.shininess > 0 ? material.shininess : 32;

    // OBJ materials reference image files next to the .mtl file.
    if (!material.diffuse_texname.empty()) {
        result.baseColorTexture = loadTexture(device, queue, (directory + material.diffuse_texname).c_str());
    }
    if (!material.specular_texname.empty()) {
        result.specularTexture = loadTexture(device, queue, (directory + material.specular_texname).c_str());
    }
    return result;
}
```

```cpp
struct Mesh {
    MTL::Buffer* vertexBuffer = nullptr;
    std::vector<Submesh> submeshes;
    std::vector<MeshMaterial> materials;        // indexed by Submesh::materialIndex

    void draw(MTL::RenderCommandEncoder* encoder, MTL::Texture* fallback) const {
        encoder->setVertexBuffer(vertexBuffer, 0, 0);
        for (const Submesh& submesh : submeshes) {
            const MeshMaterial& material = materials[submesh.materialIndex];
            encoder->setFragmentTexture(material.baseColorTexture ? material.baseColorTexture : fallback, 0);
            encoder->setFragmentTexture(material.specularTexture ? material.specularTexture : fallback, 1);
            encoder->drawIndexedPrimitives(MTL::PrimitiveTypeTriangle,
                                           submesh.indexCount,
                                           MTL::IndexTypeUInt32,
                                           submesh.indexBuffer,
                                           0);
        }
    }
};
```

```cpp
MTL::Texture* makeSolidTexture(MTL::Device* device, uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
        MTL::PixelFormatRGBA8Unorm, 1, 1, false);
    MTL::Texture* texture = device->newTexture(descriptor);
    const uint8_t pixel[4] = {r, g, b, a};
    texture->replaceRegion(MTL::Region::Make2D(0, 0, 1, 1), 0, pixel, 4);
    return texture;
}
```
