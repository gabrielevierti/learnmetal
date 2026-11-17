```cpp
#include "tiny_obj_loader.h"

class Model {
public:
    struct Node {
        Mesh mesh;
        simd::float4x4 transform;     // mesh space to model space
    };

    std::vector<Node> nodes;
    simd::float3 minBounds = { 1e30f,  1e30f,  1e30f};
    simd::float3 maxBounds = {-1e30f, -1e30f, -1e30f};

    Model(const std::string& directory, const std::string& file,
          MTL::Device* device, MTL::CommandQueue* queue) {
        tinyobj::ObjReaderConfig config;
        config.triangulate = true;
        config.mtl_search_path = directory;
        tinyobj::ObjReader reader;
        if (!reader.ParseFromFile(directory + file, config)) {
            throw std::runtime_error(reader.Error());
        }
        const tinyobj::attrib_t& attrib = reader.GetAttrib();

        std::vector<MeshMaterial> materials;
        for (const tinyobj::material_t& m : reader.GetMaterials()) {
            materials.push_back(makeMaterial(m, directory, device, queue));
        }
        if (materials.empty()) materials.push_back(MeshMaterial{});

        for (const tinyobj::shape_t& shape : reader.GetShapes()) {
            std::vector<MeshVertex> vertices;
            std::vector<uint32_t> indices;
            for (const tinyobj::index_t& index : shape.mesh.indices) {
                MeshVertex v{};
                std::memcpy(v.position, &attrib.vertices[3 * index.vertex_index], sizeof(v.position));
                if (index.normal_index >= 0)
                    std::memcpy(v.normal, &attrib.normals[3 * index.normal_index], sizeof(v.normal));
                if (index.texcoord_index >= 0) {
                    v.uv[0] = attrib.texcoords[2 * index.texcoord_index];
                    v.uv[1] = 1.0f - attrib.texcoords[2 * index.texcoord_index + 1];
                }
                simd::float3 p = {v.position[0], v.position[1], v.position[2]};
                minBounds = simd::min(minBounds, p);
                maxBounds = simd::max(maxBounds, p);
                indices.push_back(uint32_t(vertices.size()));
                vertices.push_back(v);
            }

            Mesh mesh;
            mesh.vertexBuffer = device->newBuffer(vertices.data(), sizeof(MeshVertex) * vertices.size(),
                                                  MTL::ResourceStorageModeShared);
            int materialIndex = shape.mesh.material_ids.empty() ? 0 : std::max(shape.mesh.material_ids[0], 0);
            mesh.submeshes.push_back({device->newBuffer(indices.data(), sizeof(uint32_t) * indices.size(),
                                                        MTL::ResourceStorageModeShared),
                                      indices.size(), materialIndex});
            mesh.materials = materials;

            // OBJ files have no node hierarchy, so every transform is the identity.
            // A format with a hierarchy multiplies the local transforms up to the root here.
            nodes.push_back({mesh, matrix_identity_float4x4});
        }
    }
};
```

```cpp
void drawModel(const Model& model, MTL::RenderCommandEncoder* encoder,
               simd::float4x4 modelMatrix, Uniforms& uniforms, MTL::Texture* fallback) {
    for (const Model::Node& node : model.nodes) {
        uniforms.model = modelMatrix * node.transform;
        uniforms.normalMatrix = simd::transpose(simd::inverse(upperLeft(uniforms.model)));
        encoder->setVertexBytes(&uniforms, sizeof(Uniforms), 1);
        node.mesh.draw(encoder, fallback);
    }
}
```

```cpp
// constructor
model = new Model("models/backpack/", "backpack.obj", device, commandQueue);

// draw()
encoder->setRenderPipelineState(pipelineState);
encoder->setDepthStencilState(depthState);
encoder->setFragmentBytes(&fragmentUniforms, sizeof(FragmentUniforms), 1);
encoder->setFragmentSamplerState(samplerState, 0);
drawModel(*model, encoder,
          rotation(time * 0.5f, simd::float3{0, 1, 0}),
          uniforms, whiteTexture);
```

```cpp
simd::float3 size = model->maxBounds - model->minBounds;
simd::float3 center = (model->maxBounds + model->minBounds) * 0.5f;
float scale = 2.0f / std::max(size.x, std::max(size.y, size.z));

simd::float4x4 normalize = scaling(simd::float3{scale, scale, scale}) * translation(-center);
```
