// Chapter: Getting Started / Textures
// A textured rectangle that blends two textures. Up and Down (W / S) change the mix factor.

import LearnMetalKit
import MetalKit

final class Renderer: BaseRenderer {
    let pipelineState: MTLRenderPipelineState
    let vertexBuffer: MTLBuffer
    let indexBuffer: MTLBuffer
    let crate: MTLTexture
    let checker: MTLTexture
    let samplerState: MTLSamplerState
    var mixFactor: Float = 0.2

    init(view: MTKView) {
        let device = view.device!
        let vertices: [Float] = [
            // position          // uv (0, 0 is the top left of the image)
             0.5,  0.5, 0.0,     1.0, 0.0,
             0.5, -0.5, 0.0,     1.0, 1.0,
            -0.5, -0.5, 0.0,     0.0, 1.0,
            -0.5,  0.5, 0.0,     0.0, 0.0,
        ]
        let indices: [UInt16] = [0, 1, 3, 1, 2, 3]
        vertexBuffer = device.makeBuffer(bytes: vertices,
                                         length: MemoryLayout<Float>.stride * vertices.count, options: [])!
        indexBuffer = device.makeBuffer(bytes: indices,
                                        length: MemoryLayout<UInt16>.stride * indices.count, options: [])!

        crate = Textures.crate(device: device).diffuse
        checker = Textures.checker(device: device, squares: 4,
                                   a: [1.0, 0.85, 0.3, 1], b: [0.2, 0.4, 0.9, 1])
        samplerState = makeSampler(device: device, address: .repeat)

        let floatSize = MemoryLayout<Float>.stride
        let vertexDescriptor = MTLVertexDescriptor()
        vertexDescriptor.attributes[0].format = .float3
        vertexDescriptor.attributes[0].offset = 0
        vertexDescriptor.attributes[1].format = .float2
        vertexDescriptor.attributes[1].offset = floatSize * 3
        vertexDescriptor.layouts[0].stride = floatSize * 5

        let library = makeShaderLibrary(device: device, bundle: .module)
        pipelineState = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_main",
                                     colorFormats: [view.colorPixelFormat],
                                     vertexDescriptor: vertexDescriptor)
        super.init(view: view, depth: false)
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        if Input.shared.isDown(.w) { mixFactor = min(mixFactor + deltaTime, 1) }
        if Input.shared.isDown(.s) { mixFactor = max(mixFactor - deltaTime, 0) }

        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        encoder.setRenderPipelineState(pipelineState)
        encoder.setVertexBuffer(vertexBuffer, offset: 0, index: 0)
        encoder.setFragmentTexture(crate, index: 0)
        encoder.setFragmentTexture(checker, index: 1)
        encoder.setFragmentSamplerState(samplerState, index: 0)
        encoder.setFragmentValue(mixFactor, index: 0)
        encoder.drawIndexedPrimitives(type: .triangle, indexCount: 6, indexType: .uint16,
                                      indexBuffer: indexBuffer, indexBufferOffset: 0)
        encoder.endEncoding()
    }
}

runApp(title: "04 Textures (W / S: mix factor)") { view in Renderer(view: view) }
