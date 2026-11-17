```cpp
// Add a tangent to the vertex struct from Model Loading.
struct MeshVertex {
    float position[3];
    float normal[3];
    float uv[2];
    float tangent[3];
};

vertexDescriptor->attributes()->object(3)->setFormat(MTL::VertexFormatFloat3);   // tangent
vertexDescriptor->attributes()->object(3)->setOffset(offsetof(MeshVertex, tangent));
vertexDescriptor->layouts()->object(0)->setStride(sizeof(MeshVertex));           // 44 bytes
```

```cpp
// Without Model I/O, compute one tangent per triangle and store it in its three vertices.
for (size_t i = 0; i + 2 < vertices.size(); i += 3) {
    MeshVertex& a = vertices[i]; MeshVertex& b = vertices[i + 1]; MeshVertex& c = vertices[i + 2];
    simd::float3 e1 = {b.position[0] - a.position[0], b.position[1] - a.position[1], b.position[2] - a.position[2]};
    simd::float3 e2 = {c.position[0] - a.position[0], c.position[1] - a.position[1], c.position[2] - a.position[2]};
    float du1 = b.uv[0] - a.uv[0], dv1 = b.uv[1] - a.uv[1];
    float du2 = c.uv[0] - a.uv[0], dv2 = c.uv[1] - a.uv[1];

    float f = 1.0f / (du1 * dv2 - du2 * dv1);
    simd::float3 tangent = simd::normalize(f * (dv2 * e1 - dv1 * e2));
    for (MeshVertex* v : {&a, &b, &c}) {
        v->tangent[0] = tangent.x; v->tangent[1] = tangent.y; v->tangent[2] = tangent.z;
    }
}
```

```cpp
float f = 1.0f / (du1 * dv2 - du2 * dv1);
simd::float3 tangent = simd::normalize(f * (dv2 * e1 - dv1 * e2));
```
