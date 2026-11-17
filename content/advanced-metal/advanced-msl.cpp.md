```cpp
MTL::FunctionConstantValues* constants = MTL::FunctionConstantValues::alloc()->init();
bool useNormalMap = true;
constants->setConstantValue(&useNormalMap, MTL::DataTypeBool, NS::UInteger(0));
int32_t lightCount = 4;
constants->setConstantValue(&lightCount, MTL::DataTypeInt, NS::UInteger(1));

NS::Error* error = nullptr;
MTL::Function* function = library->newFunction(MTLSTR("fragment_main"), constants, &error);
```
