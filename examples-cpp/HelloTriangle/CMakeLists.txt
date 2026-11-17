cmake_minimum_required(VERSION 3.20)
project(LearnMetal LANGUAGES CXX OBJCXX)
set(CMAKE_CXX_STANDARD 17)

find_package(glfw3 REQUIRED)

# Download metal-cpp from https://developer.apple.com/metal/cpp/ and unzip it here as metal-cpp/.
add_executable(LearnMetal main.cpp Renderer.cpp metal_impl.cpp glfw_bridge.mm)
target_include_directories(LearnMetal PRIVATE metal-cpp)
target_link_libraries(LearnMetal PRIVATE glfw
    "-framework Metal" "-framework Foundation" "-framework QuartzCore" "-framework Cocoa")

# Copy the shader source next to the executable; it is compiled when the app starts.
configure_file(Shaders.metal ${CMAKE_BINARY_DIR}/Shaders.metal COPYONLY)
