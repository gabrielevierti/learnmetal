#include "Renderer.hpp"

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>

// Compiles a .metal source file at launch. Errors are printed with their line number.
static MTL::Library* loadLibrary(MTL::Device* device, const char* path) {
    std::ifstream file(path);
    std::stringstream source;
    source << file.rdbuf();

    NS::Error* error = nullptr;
    MTL::Library* library = device->newLibrary(
        NS::String::string(source.str().c_str(), NS::UTF8StringEncoding), nullptr, &error);
    if (!library) {
        std::cerr << "Shader error: " << error->localizedDescription()->utf8String() << "\n";
        std::exit(1);
    }
    return library;
}

Renderer::Renderer(MTL::Device* device, CA::MetalLayer* layer)
    : device(device->retain()), layer(layer) {
    commandQueue = device->newCommandQueue();
    layer->setPixelFormat(MTL::PixelFormatBGRA8Unorm);

    const float vertices[] = {
        -0.5f, -0.5f, 0.0f,   // bottom left
         0.5f, -0.5f, 0.0f,   // bottom right
         0.0f,  0.5f, 0.0f,   // top
    };
    vertexBuffer = device->newBuffer(vertices, sizeof(vertices), MTL::ResourceStorageModeShared);

    MTL::VertexDescriptor* vertexDescriptor = MTL::VertexDescriptor::alloc()->init();
    vertexDescriptor->attributes()->object(0)->setFormat(MTL::VertexFormatFloat3);
    vertexDescriptor->attributes()->object(0)->setOffset(0);
    vertexDescriptor->attributes()->object(0)->setBufferIndex(0);
    vertexDescriptor->layouts()->object(0)->setStride(sizeof(float) * 3);

    MTL::Library* library = loadLibrary(device, "Shaders.metal");
    MTL::Function* vertexFunction = library->newFunction(MTLSTR("vertex_main"));
    MTL::Function* fragmentFunction = library->newFunction(MTLSTR("fragment_main"));

    MTL::RenderPipelineDescriptor* pipelineDescriptor = MTL::RenderPipelineDescriptor::alloc()->init();
    pipelineDescriptor->setVertexFunction(vertexFunction);
    pipelineDescriptor->setFragmentFunction(fragmentFunction);
    pipelineDescriptor->setVertexDescriptor(vertexDescriptor);
    pipelineDescriptor->colorAttachments()->object(0)->setPixelFormat(MTL::PixelFormatBGRA8Unorm);

    NS::Error* error = nullptr;
    pipelineState = device->newRenderPipelineState(pipelineDescriptor, &error);
    if (!pipelineState) {
        std::cerr << "Could not create pipeline state: "
                  << error->localizedDescription()->utf8String() << "\n";
        std::exit(1);
    }

    pipelineDescriptor->release();
    vertexFunction->release();
    fragmentFunction->release();
    library->release();
    vertexDescriptor->release();
}

Renderer::~Renderer() {
    vertexBuffer->release();
    pipelineState->release();
    commandQueue->release();
    device->release();
}

void Renderer::draw() {
    // Objects returned by methods that do not start with new/alloc are autoreleased.
    NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();

    CA::MetalDrawable* drawable = layer->nextDrawable();
    if (drawable) {
        MTL::RenderPassDescriptor* passDescriptor = MTL::RenderPassDescriptor::alloc()->init();
        MTL::RenderPassColorAttachmentDescriptor* color = passDescriptor->colorAttachments()->object(0);
        color->setTexture(drawable->texture());
        color->setLoadAction(MTL::LoadActionClear);
        color->setClearColor(MTL::ClearColor::Make(0.2, 0.3, 0.3, 1.0));
        color->setStoreAction(MTL::StoreActionStore);

        MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();
        MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(passDescriptor);

        encoder->setRenderPipelineState(pipelineState);
        encoder->setVertexBuffer(vertexBuffer, 0, 0);
        encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(3));

        encoder->endEncoding();
        commandBuffer->presentDrawable(drawable);
        commandBuffer->commit();
        passDescriptor->release();
    }
    pool->release();
}
