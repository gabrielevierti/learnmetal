// Chapter: Getting Started / Shaders
// Per-vertex colors interpolated across a triangle, plus a uniform that pulses over time.

import LearnMetalKit
import MetalKit

struct Uniforms {
    var time: Float
    var tint: SIMD4<Float>
}

final class Renderer: NSObject, MTKViewDelegate {
    let device: MTLDevice
    let commandQueue: MTLCommandQueue
    let pipelineState: MTLRenderPipelineState
    let vertexBuffer: MTLBuffer
    let startTime = CACurrentMediaTime()

    init(view: MTKView) {
        device = view.device!
        commandQueue = device.makeCommandQueue()!

        let vertices: [Float] = [
            // position         // color
            -0.5, -0.5, 0.0,    1.0, 0.0, 0.0,
             0.5, -0.5, 0.0,    0.0, 1.0, 0.0,
             0.0,  0.5, 0.0,    0.0, 0.0, 1.0,
        ]
        vertexBuffer = device.makeBuffer(bytes: vertices,
                                         length: MemoryLayout<Float>.stride * vertices.count, options: [])!

        let floatSize = MemoryLayout<Float>.stride
        let vertexDescriptor = MTLVertexDescriptor()
        vertexDescriptor.attributes[0].format = .float3
        vertexDescriptor.attributes[0].offset = 0
        vertexDescriptor.attributes[0].bufferIndex = 0
        vertexDescriptor.attributes[1].format = .float3
        vertexDescriptor.attributes[1].offset = floatSize * 3
        vertexDescriptor.attributes[1].bufferIndex = 0
        vertexDescriptor.layouts[0].stride = floatSize * 6

        let library = makeShaderLibrary(device: device, bundle: .module)
        pipelineState = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_main",
                                     colorFormats: [view.colorPixelFormat],
                                     vertexDescriptor: vertexDescriptor)
        super.init()
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}

    func draw(in view: MTKView) {
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let drawable = view.currentDrawable,
              let commandBuffer = commandQueue.makeCommandBuffer(),
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else {
            return
        }

        var uniforms = Uniforms(time: Float(CACurrentMediaTime() - startTime), tint: [1, 1, 1, 1])

        encoder.setRenderPipelineState(pipelineState)
        encoder.setVertexBuffer(vertexBuffer, offset: 0, index: 0)
        encoder.setFragmentBytes(&uniforms, length: MemoryLayout<Uniforms>.stride, index: 0)
        encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)

        encoder.endEncoding()
        commandBuffer.present(drawable)
        commandBuffer.commit()
    }
}

runApp(title: "03 Shaders") { view in Renderer(view: view) }
