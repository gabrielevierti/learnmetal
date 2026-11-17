```cpp
// The same 32-byte layout, as a plain struct. Arrays of float pack tightly: 12 + 12 + 8.
struct MeshVertex {
    float position[3];
    float normal[3];
    float uv[2];
};

MTL::VertexDescriptor* vertexDescriptor = MTL::VertexDescriptor::alloc()->init();
vertexDescriptor->attributes()->object(0)->setFormat(MTL::VertexFormatFloat3);   // position
vertexDescriptor->attributes()->object(0)->setOffset(offsetof(MeshVertex, position));
vertexDescriptor->attributes()->object(1)->setFormat(MTL::VertexFormatFloat3);   // normal
vertexDescriptor->attributes()->object(1)->setOffset(offsetof(MeshVertex, normal));
vertexDescriptor->attributes()->object(2)->setFormat(MTL::VertexFormatFloat2);   // uv
vertexDescriptor->attributes()->object(2)->setOffset(offsetof(MeshVertex, uv));
vertexDescriptor->layouts()->object(0)->setStride(sizeof(MeshVertex));
```

```cpp
#define TINYOBJLOADER_IMPLEMENTATION
#include "tiny_obj_loader.h"

tinyobj::ObjReaderConfig config;
config.triangulate = true;                      // quads and n-gons become triangles
config.mtl_search_path = "models/backpack/";    // where the .mtl file and textures live

tinyobj::ObjReader reader;
if (!reader.ParseFromFile("models/backpack/backpack.obj", config)) {
    std::cerr << "Could not load model: " << reader.Error() << "\n";
    std::exit(1);
}
const tinyobj::attrib_t& attrib = reader.GetAttrib();
const std::vector<tinyobj::shape_t>& shapes = reader.GetShapes();
const std::vector<tinyobj::material_t>& materials = reader.GetMaterials();
```

```cpp
// Textures are loaded later, per material, with loadTexture() from the Textures chapter.

// Generate a flat normal for a triangle whose file has none.
simd::float3 faceNormal(simd::float3 a, simd::float3 b, simd::float3 c) {
    return simd::normalize(simd::cross(b - a, c - a));
}
```

```cpp
// Turn one tinyobj shape into Metal buffers. Every face corner becomes a vertex.
std::vector<MeshVertex> vertices;
std::vector<uint32_t> indices;
for (const tinyobj::index_t& index : shape.mesh.indices) {
    MeshVertex v{};
    std::memcpy(v.position, &attrib.vertices[3 * index.vertex_index], sizeof(v.position));
    if (index.normal_index >= 0) {
        std::memcpy(v.normal, &attrib.normals[3 * index.normal_index], sizeof(v.normal));
    }
    if (index.texcoord_index >= 0) {
        v.uv[0] = attrib.texcoords[2 * index.texcoord_index];
        v.uv[1] = 1.0f - attrib.texcoords[2 * index.texcoord_index + 1];   // OBJ has v pointing up
    }
    indices.push_back(uint32_t(vertices.size()));
    vertices.push_back(v);
}

MTL::Buffer* vertexBuffer = device->newBuffer(vertices.data(), sizeof(MeshVertex) * vertices.size(),
                                              MTL::ResourceStorageModeShared);
MTL::Buffer* indexBuffer = device->newBuffer(indices.data(), sizeof(uint32_t) * indices.size(),
                                             MTL::ResourceStorageModeShared);
```

```cpp
// Without Model I/O, a test sphere is a few lines of trigonometry.
std::vector<MeshVertex> makeSphere(float radius, int segments) {
    std::vector<MeshVertex> vertices;
    auto corner = [&](int i, int j) {
        float theta = float(i) / segments * float(M_PI);
        float phi = float(j) / segments * 2.0f * float(M_PI);
        simd::float3 n = {std::sin(theta) * std::cos(phi), std::cos(theta), std::sin(theta) * std::sin(phi)};
        return MeshVertex{{n.x * radius, n.y * radius, n.z * radius}, {n.x, n.y, n.z},
                          {float(j) / segments, float(i) / segments}};
    };
    for (int i = 0; i < segments; i++) {
        for (int j = 0; j < segments; j++) {
            MeshVertex a = corner(i, j), b = corner(i + 1, j), c = corner(i + 1, j + 1), d = corner(i, j + 1);
            vertices.insert(vertices.end(), {a, c, b, a, d, c});      // two counter-clockwise triangles
        }
    }
    return vertices;
}
```
