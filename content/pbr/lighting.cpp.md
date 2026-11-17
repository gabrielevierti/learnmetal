```cpp
// makeSphere() from the Model I/O chapter, drawn without an index buffer.
std::vector<MeshVertex> sphere = makeSphere(0.5f, 64);
sphereBuffer = device->newBuffer(sphere.data(), sizeof(MeshVertex) * sphere.size(),
                                 MTL::ResourceStorageModeShared);
sphereVertexCount = sphere.size();
```

```cpp
const int rows = 7, columns = 7;
for (int row = 0; row < rows; row++) {
    pbrUniforms.metallic = float(row) / float(rows - 1);
    for (int column = 0; column < columns; column++) {
        // A roughness of exactly 0 gives an infinitely small highlight; clamp it.
        pbrUniforms.roughness = std::max(float(column) / float(columns - 1), 0.05f);
        uniforms.model = translation(simd::float3{float(column - columns / 2) * 2.5f,
                                                  float(row - rows / 2) * 2.5f, 0});
        // set uniforms, draw the sphere
    }
}
```
