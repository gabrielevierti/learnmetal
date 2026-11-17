#pragma once
#include <Metal/Metal.hpp>
#include <QuartzCore/QuartzCore.hpp>

class Renderer {
public:
    Renderer(MTL::Device* device, CA::MetalLayer* layer);
    ~Renderer();

    void resize(int width, int height) {}
    void draw();

private:
    MTL::Device* device;
    MTL::CommandQueue* commandQueue;
    CA::MetalLayer* layer;
    MTL::RenderPipelineState* pipelineState = nullptr;
    MTL::Buffer* vertexBuffer = nullptr;
};
