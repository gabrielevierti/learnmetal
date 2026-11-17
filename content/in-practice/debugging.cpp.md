```cpp
sceneColor->setLabel(MTLSTR("Scene HDR Color"));
pipelineDescriptor->setLabel(MTLSTR("PBR Opaque Pipeline"));
commandBuffer->setLabel(MTLSTR("Frame"));
encoder->setLabel(MTLSTR("Shadow Pass"));
vertexBuffer->setLabel(MTLSTR("Cube Vertices"));
```

```cpp
encoder->pushDebugGroup(MTLSTR("Draw Opaque Models"));
for (const Model& model : models) {
    encoder->pushDebugGroup(NS::String::string(model.name.c_str(), NS::UTF8StringEncoding));
    drawModel(model, encoder);
    encoder->popDebugGroup();
}
encoder->popDebugGroup();

encoder->insertDebugSignpost(MTLSTR("Before skybox"));
```

```cpp
MTL::CaptureDescriptor* captureDescriptor = MTL::CaptureDescriptor::alloc()->init();
captureDescriptor->setCaptureObject(device);
NS::Error* error = nullptr;
MTL::CaptureManager::sharedCaptureManager()->startCapture(captureDescriptor, &error);
// ...render a frame...
MTL::CaptureManager::sharedCaptureManager()->stopCapture();
```

```cpp
commandBuffer->addCompletedHandler([](MTL::CommandBuffer* buffer) {
    if (NS::Error* error = buffer->error()) {
        std::cerr << "Command buffer failed: " << error->localizedDescription()->utf8String() << "\n";
    }
});
```
