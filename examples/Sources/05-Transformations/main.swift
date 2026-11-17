// Chapter: Getting Started / Transformations
// One rectangle drawn twice with different matrices: scale, then rotate, then translate.

import LearnMetalKit
import MetalKit

final class Renderer: BaseRenderer {
    let pipelineState: MTLRenderPipelineState
    let vertexBuffer: MTLBuffer
    let indexBuffer: MTLBuffer
    let texture: MTLTexture
    let samplerState: MTLSamplerState

    init(view: MTKView) {
        let device = view.device!
        let vertices: [Float] = [
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
        texture = Textures.crate(device: device).diffuse
        samplerState = makeSampler(device: device)

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
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        encoder.setRenderPipelineState(pipelineState)
        encoder.setVertexBuffer(vertexBuffer, offset: 0, index: 0)
        encoder.setFragmentTexture(texture, index: 0)
        encoder.setFragmentSamplerState(samplerState, index: 0)

        // Bottom right: spins around its own center.
        let spinning = float4x4(translation: [0.5, -0.5, 0])
                     * float4x4(rotation: time, axis: [0, 0, 1])
                     * float4x4(scale: 0.5)
        // Top left: pulses in size.
        let pulsing = float4x4(translation: [-0.5, 0.5, 0])
                    * float4x4(scale: 0.3 + 0.2 * abs(sin(time)))

        for transform in [spinning, pulsing] {
            encoder.setVertexValue(transform, index: 1)
            encoder.drawIndexedPrimitives(type: .triangle, indexCount: 6, indexType: .uint16,
                                          indexBuffer: indexBuffer, indexBufferOffset: 0)
        }
        encoder.endEncoding()
    }
}

runApp(title: "05 Transformations") { view in Renderer(view: view) }
