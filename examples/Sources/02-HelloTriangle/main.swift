// Chapter: Getting Started / Hello Triangle
// A triangle, then an indexed rectangle. Press Space to switch, W to toggle wireframe.

import LearnMetalKit
import MetalKit

final class Renderer: NSObject, MTKViewDelegate {
    let device: MTLDevice
    let commandQueue: MTLCommandQueue
    let pipelineState: MTLRenderPipelineState
    let triangleBuffer: MTLBuffer
    let rectangleBuffer: MTLBuffer
    let indexBuffer: MTLBuffer
    let indexCount: Int

    var showRectangle = false
    var wireframe = false

    init(view: MTKView) {
        device = view.device!
        commandQueue = device.makeCommandQueue()!

        let triangle: [Float] = [
            -0.5, -0.5, 0.0,
             0.5, -0.5, 0.0,
             0.0,  0.5, 0.0,
        ]
        let rectangle: [Float] = [
             0.5,  0.5, 0.0,   // top right
             0.5, -0.5, 0.0,   // bottom right
            -0.5, -0.5, 0.0,   // bottom left
            -0.5,  0.5, 0.0,   // top left
        ]
        let indices: [UInt16] = [0, 1, 3, 1, 2, 3]

        triangleBuffer = device.makeBuffer(bytes: triangle,
                                           length: MemoryLayout<Float>.stride * triangle.count, options: [])!
        rectangleBuffer = device.makeBuffer(bytes: rectangle,
                                            length: MemoryLayout<Float>.stride * rectangle.count, options: [])!
        indexBuffer = device.makeBuffer(bytes: indices,
                                        length: MemoryLayout<UInt16>.stride * indices.count, options: [])!
        indexCount = indices.count

        let vertexDescriptor = MTLVertexDescriptor()
        vertexDescriptor.attributes[0].format = .float3
        vertexDescriptor.attributes[0].offset = 0
        vertexDescriptor.attributes[0].bufferIndex = 0
        vertexDescriptor.layouts[0].stride = MemoryLayout<Float>.stride * 3

        let library = makeShaderLibrary(device: device, bundle: .module)
        let pipelineDescriptor = MTLRenderPipelineDescriptor()
        pipelineDescriptor.vertexFunction = library.makeFunction(name: "vertex_main")
        pipelineDescriptor.fragmentFunction = library.makeFunction(name: "fragment_main")
        pipelineDescriptor.vertexDescriptor = vertexDescriptor
        pipelineDescriptor.colorAttachments[0].pixelFormat = view.colorPixelFormat
        do {
            pipelineState = try device.makeRenderPipelineState(descriptor: pipelineDescriptor)
        } catch {
            fatalError("Could not create pipeline state: \(error)")
        }
        super.init()
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}

    func draw(in view: MTKView) {
        if Input.shared.wasPressed(.space) { showRectangle.toggle() }
        if Input.shared.wasPressed(.w) { wireframe.toggle() }

        guard let passDescriptor = view.currentRenderPassDescriptor,
              let drawable = view.currentDrawable,
              let commandBuffer = commandQueue.makeCommandBuffer(),
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else {
            return
        }

        encoder.setRenderPipelineState(pipelineState)
        encoder.setTriangleFillMode(wireframe ? .lines : .fill)
        if showRectangle {
            encoder.setVertexBuffer(rectangleBuffer, offset: 0, index: 0)
            encoder.drawIndexedPrimitives(type: .triangle, indexCount: indexCount, indexType: .uint16,
                                          indexBuffer: indexBuffer, indexBufferOffset: 0)
        } else {
            encoder.setVertexBuffer(triangleBuffer, offset: 0, index: 0)
            encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
        }

        encoder.endEncoding()
        commandBuffer.present(drawable)
        commandBuffer.commit()
    }
}

runApp(title: "02 Hello Triangle (Space: rectangle, W: wireframe)") { view in Renderer(view: view) }
