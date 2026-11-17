```cpp
const float vertices[] = {
    -0.5f, -0.5f, 0.0f,   // 1
     0.5f, -0.5f, 0.0f,   // 2
     0.0f,  0.5f, 0.0f,   // 3   -> counter-clockwise when seen from +z
};
```

```cpp
encoder->setFrontFacingWinding(MTL::WindingCounterClockwise);
encoder->setCullMode(MTL::CullModeBack);
```
