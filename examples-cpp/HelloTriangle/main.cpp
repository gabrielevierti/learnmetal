// Chapters: Getting Started / Project Setup, Hello View, Hello Triangle (C++ with metal-cpp)

#include <GLFW/glfw3.h>
#include "Renderer.hpp"

void* attachMetalLayer(GLFWwindow* window, void* device);

int main() {
    glfwInit();
    glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API);        // no OpenGL context
    GLFWwindow* window = glfwCreateWindow(800, 600, "LearnMetal", nullptr, nullptr);

    MTL::Device* device = MTL::CreateSystemDefaultDevice();
    auto* layer = static_cast<CA::MetalLayer*>(attachMetalLayer(window, device));
    {
        Renderer renderer(device, layer);

        while (!glfwWindowShouldClose(window)) {
            glfwPollEvents();

            // The drawable follows the window size, in pixels.
            int width, height;
            glfwGetFramebufferSize(window, &width, &height);
            layer->setDrawableSize(CGSizeMake(width, height));
            renderer.resize(width, height);

            renderer.draw();
        }
    }
    device->release();
    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}
