```cpp
/// Right-handed perspective projection with a 0...1 depth range.
inline simd::float4x4 perspective(float fovY, float aspect, float near, float far) {
    float y = 1.0f / std::tan(fovY * 0.5f);
    float x = y / aspect;
    float z = far / (near - far);
    return simd_matrix(simd_make_float4(x, 0, 0,  0),
                       simd_make_float4(0, y, 0,  0),
                       simd_make_float4(0, 0, z, -1),
                       simd_make_float4(0, 0, z * near, 0));
}
```

```cpp
struct Uniforms {
    simd::float4x4 model;
    simd::float4x4 view;
    simd::float4x4 projection;
};
```

```cpp
float aspect = 1.0f;      // member of Renderer

void Renderer::resize(int width, int height) {
    aspect = float(width) / float(height);
}
```

```cpp
simd::float4x4 model = rotation(time, simd::float3{0.5f, 1, 0});
simd::float4x4 viewMatrix = translation(simd::float3{0, 0, -3});
simd::float4x4 projection = perspective(radians(45), aspect, 0.1f, 100.0f);
Uniforms uniforms{ model, viewMatrix, projection };
```

```cpp
#include <vector>

struct Vertex {
    simd::float3 position;
    simd::float3 normal;
    simd::float2 uv;
};

std::vector<Vertex> makeCube() {
    struct Face { simd::float3 normal, right, up; };
    const Face faces[] = {
        {{ 0,  0,  1}, { 1, 0,  0}, {0, 1,  0}},   // front
        {{ 0,  0, -1}, {-1, 0,  0}, {0, 1,  0}},   // back
        {{ 1,  0,  0}, { 0, 0, -1}, {0, 1,  0}},   // right
        {{-1,  0,  0}, { 0, 0,  1}, {0, 1,  0}},   // left
        {{ 0,  1,  0}, { 1, 0,  0}, {0, 0, -1}},   // top
        {{ 0, -1,  0}, { 1, 0,  0}, {0, 0,  1}},   // bottom
    };
    const simd::float2 corners[] = {{-1, -1}, {1, -1}, {1, 1}, {-1, -1}, {1, 1}, {-1, 1}};

    std::vector<Vertex> vertices;
    for (const Face& face : faces) {
        for (simd::float2 c : corners) {
            simd::float3 position = (face.normal + face.right * c.x + face.up * c.y) * 0.5f;
            simd::float2 uv = {c.x * 0.5f + 0.5f, 0.5f - c.y * 0.5f};
            vertices.push_back({position, face.normal, uv});
        }
    }
    return vertices;
}
```

```cpp
vertexDescriptor->attributes()->object(0)->setFormat(MTL::VertexFormatFloat3);
vertexDescriptor->attributes()->object(0)->setOffset(offsetof(Vertex, position));
vertexDescriptor->attributes()->object(1)->setFormat(MTL::VertexFormatFloat3);
vertexDescriptor->attributes()->object(1)->setOffset(offsetof(Vertex, normal));
vertexDescriptor->attributes()->object(2)->setFormat(MTL::VertexFormatFloat2);
vertexDescriptor->attributes()->object(2)->setOffset(offsetof(Vertex, uv));
vertexDescriptor->layouts()->object(0)->setStride(sizeof(Vertex));
```

```cpp
// 1. Create a depth texture the size of the drawable. Without MTKView this is our job;
//    recreate it in resize().
MTL::TextureDescriptor* depthTextureDescriptor = MTL::TextureDescriptor::texture2DDescriptor(
    MTL::PixelFormatDepth32Float, width, height, false);
depthTextureDescriptor->setUsage(MTL::TextureUsageRenderTarget);
depthTextureDescriptor->setStorageMode(MTL::StorageModePrivate);
depthTexture = device->newTexture(depthTextureDescriptor);

//    ...and attach it to the render pass in draw().
passDescriptor->depthAttachment()->setTexture(depthTexture);
passDescriptor->depthAttachment()->setLoadAction(MTL::LoadActionClear);
passDescriptor->depthAttachment()->setClearDepth(1.0);
passDescriptor->depthAttachment()->setStoreAction(MTL::StoreActionDontCare);

// 2. Tell the pipeline about it.
pipelineDescriptor->setDepthAttachmentPixelFormat(MTL::PixelFormatDepth32Float);

// 3. Create a depth-stencil state...
MTL::DepthStencilDescriptor* depthDescriptor = MTL::DepthStencilDescriptor::alloc()->init();
depthDescriptor->setDepthCompareFunction(MTL::CompareFunctionLess);
depthDescriptor->setDepthWriteEnabled(true);
depthState = device->newDepthStencilState(depthDescriptor);
depthDescriptor->release();
```

```cpp
// ...and set it when drawing.
encoder->setDepthStencilState(depthState);
```

```cpp
const simd::float3 cubePositions[] = {
    { 0.0f,  0.0f,   0.0f}, { 2.0f,  5.0f, -15.0f}, {-1.5f, -2.2f, -2.5f}, {-3.8f, -2.0f, -12.3f},
    { 2.4f, -0.4f,  -3.5f}, {-1.7f,  3.0f,  -7.5f}, { 1.3f, -2.0f, -2.5f}, { 1.5f,  2.0f,  -2.5f},
    { 1.5f,  0.2f,  -1.5f}, {-1.3f,  1.0f,  -1.5f},
};

for (int i = 0; i < 10; i++) {
    uniforms.model = translation(cubePositions[i])
                   * rotation(radians(20.0f * i), simd::float3{1, 0.3f, 0.5f});
    encoder->setVertexBytes(&uniforms, sizeof(Uniforms), 1);
    encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(36));
}
```
