```cpp
if (!device->supportsRaytracing()) { /* fall back to shadow maps */ return; }
```

```cpp
MTL::AccelerationStructureTriangleGeometryDescriptor* geometry =
    MTL::AccelerationStructureTriangleGeometryDescriptor::alloc()->init();
geometry->setVertexBuffer(mesh.vertexBuffer);
geometry->setVertexBufferOffset(0);
geometry->setVertexStride(sizeof(MeshVertex));        // positions are at offset 0
geometry->setIndexBuffer(submesh.indexBuffer);
geometry->setIndexBufferOffset(0);
geometry->setIndexType(MTL::IndexTypeUInt32);
geometry->setTriangleCount(submesh.indexCount / 3);

MTL::PrimitiveAccelerationStructureDescriptor* descriptor =
    MTL::PrimitiveAccelerationStructureDescriptor::alloc()->init();
descriptor->setGeometryDescriptors(NS::Array::array(geometry));
```

```cpp
MTL::AccelerationStructureSizes sizes = device->accelerationStructureSizes(descriptor);
MTL::AccelerationStructure* accelerationStructure =
    device->newAccelerationStructure(sizes.accelerationStructureSize);
MTL::Buffer* scratch = device->newBuffer(sizes.buildScratchBufferSize, MTL::ResourceStorageModePrivate);

MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();
MTL::AccelerationStructureCommandEncoder* encoder = commandBuffer->accelerationStructureCommandEncoder();
encoder->buildAccelerationStructure(accelerationStructure, descriptor, scratch, 0);
encoder->endEncoding();
commandBuffer->commit();
```

```cpp
computeEncoder->setAccelerationStructure(accelerationStructure, 1);
```

```cpp
encoder->setFragmentAccelerationStructure(accelerationStructure, 3);
```
