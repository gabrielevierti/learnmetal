```cpp
encoder->setVertexBuffer(particleBuffer, 0, 0);
encoder->drawPrimitives(MTL::PrimitiveTypeTriangleStrip,
                        NS::UInteger(0),                  // vertex start
                        NS::UInteger(4),                  // vertex count
                        NS::UInteger(particleCount));     // instance count
```

```cpp
encoder->drawPrimitives(MTL::PrimitiveTypeLine, NS::UInteger(0), NS::UInteger(vertexCount * 2));
```
