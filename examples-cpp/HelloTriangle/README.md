# learnmetal C++ starter

The Hello Triangle chapter in C++ with Apple's metal-cpp and GLFW.

1. `brew install glfw cmake`
2. Download metal-cpp from https://developer.apple.com/metal/cpp/ and unzip it into this folder as `metal-cpp/`.
3. Build and run:

```sh
cmake -B build && cmake --build build
cd build && MTL_DEBUG_LAYER=1 ./LearnMetal
```

Run from the `build` folder: `Shaders.metal` is loaded from the current directory and compiled at launch.
