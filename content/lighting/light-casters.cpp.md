```cpp
light.cutOff = std::cos(radians(12.5f));
light.outerCutOff = std::cos(radians(17.5f));
```

```cpp
light.position = camera.position;
light.direction = camera.front();
```
