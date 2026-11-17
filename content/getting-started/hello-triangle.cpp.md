```cpp
const float vertices[] = {
    -0.5f, -0.5f, 0.0f,   // bottom left
     0.5f, -0.5f, 0.0f,   // bottom right
     0.0f,  0.5f, 0.0f,   // top
};
```

```cpp
MTL::Buffer* vertexBuffer;      // member of Renderer

// in the constructor
vertexBuffer = device->newBuffer(vertices, sizeof(vertices), MTL::ResourceStorageModeShared);
```

```cpp
MTL::VertexDescriptor* vertexDescriptor = MTL::VertexDescriptor::alloc()->init();
vertexDescriptor->attributes()->object(0)->setFormat(MTL::VertexFormatFloat3);
vertexDescriptor->attributes()->object(0)->setOffset(0);
vertexDescriptor->attributes()->object(0)->setBufferIndex(0);
vertexDescriptor->layouts()->object(0)->setStride(sizeof(float) * 3);
```

```cpp
MTL::RenderPipelineState* pipelineState;      // member of Renderer

// in the constructor
MTL::Library* library = loadLibrary(device, "Shaders.metal");   // from Project Setup

MTL::RenderPipelineDescriptor* pipelineDescriptor = MTL::RenderPipelineDescriptor::alloc()->init();
pipelineDescriptor->setVertexFunction(library->newFunction(MTLSTR("vertex_main")));
pipelineDescriptor->setFragmentFunction(library->newFunction(MTLSTR("fragment_main")));
pipelineDescriptor->setVertexDescriptor(vertexDescriptor);
pipelineDescriptor->colorAttachments()->object(0)->setPixelFormat(MTL::PixelFormatBGRA8Unorm);

NS::Error* error = nullptr;
pipelineState = device->newRenderPipelineState(pipelineDescriptor, &error);
if (!pipelineState) {
    std::cerr << "Could not create pipeline state: "
              << error->localizedDescription()->utf8String() << "\n";
    std::exit(1);
}
pipelineDescriptor->release();
vertexDescriptor->release();
library->release();
```

```cpp
encoder->setRenderPipelineState(pipelineState);
encoder->setVertexBuffer(vertexBuffer, 0, 0);       // buffer, offset, index
encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(3));
```

```cpp
const float vertices[] = {
     0.5f,  0.5f, 0.0f,   // top right
     0.5f, -0.5f, 0.0f,   // bottom right
    -0.5f, -0.5f, 0.0f,   // bottom left
    -0.5f,  0.5f, 0.0f,   // top left
};
const uint16_t indices[] = {
    0, 1, 3,
    1, 2, 3,
};

indexBuffer = device->newBuffer(indices, sizeof(indices), MTL::ResourceStorageModeShared);
```

```cpp
encoder->drawIndexedPrimitives(MTL::PrimitiveTypeTriangle,
                               6,                        // index count
                               MTL::IndexTypeUInt16,
                               indexBuffer,
                               0);                       // index buffer offset
```
