```cpp
diffuseMap = loadTexture(device, commandQueue, "container2.png");
specularMap = loadTexture(device, commandQueue, "container2_specular.png");
```

```cpp
encoder->setFragmentTexture(diffuseMap, 0);
encoder->setFragmentTexture(specularMap, 1);
encoder->setFragmentSamplerState(samplerState, 0);
```
