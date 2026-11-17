#import <Cocoa/Cocoa.h>
#import <Metal/Metal.h>
#import <QuartzCore/CAMetalLayer.h>
#define GLFW_EXPOSE_NATIVE_COCOA
#include <GLFW/glfw3.h>
#include <GLFW/glfw3native.h>

// Gives the GLFW window a CAMetalLayer and returns it. The view keeps the layer alive.
void* attachMetalLayer(GLFWwindow* window, void* device) {
    NSWindow* nsWindow = glfwGetCocoaWindow(window);
    CAMetalLayer* layer = [CAMetalLayer layer];
    layer.device = (__bridge id<MTLDevice>)device;
    layer.pixelFormat = MTLPixelFormatBGRA8Unorm;
    nsWindow.contentView.wantsLayer = YES;
    nsWindow.contentView.layer = layer;
    return (__bridge void*)layer;
}
