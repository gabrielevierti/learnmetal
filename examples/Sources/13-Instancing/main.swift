// Chapter: Advanced Metal / Instancing
// A ring of 20,000 rocks around a planet, drawn with a single instanced draw call.
// Per-instance data lives in a buffer and is indexed with [[instance_id]].

import LearnMetalKit
import MetalKit

struct InstanceData {
    var model: float4x4
    var color: SIMD4<Float>
}

struct FrameUniforms {
    var view: float4x4
    var projection: float4x4
    var time: Float
}

final class Renderer: BaseRenderer {
    let pipelineState: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    let sphere: MTKMesh
    let rockBuffer: MTLBuffer
    let planetBuffer: MTLBuffer
    let rockCount = 20_000

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        sphere = Geometry.sphere(device: device, radius: 5)
        depthState = makeDepthState(device: device)

        var rocks: [InstanceData] = []
        rocks.reserveCapacity(rockCount)
        for i in 0..<rockCount {
            let angle = Float(i) / Float(rockCount) * 2 * .pi
            let radius = 17 + Float.random(in: -3...3)
            let position = Float3(sin(angle) * radius, Float.random(in: -0.8...0.8), cos(angle) * radius)
            let model = float4x4(translation: position)
                      * float4x4(rotation: Float.random(in: 0...(2 * .pi)), axis: [0.4, 0.6, 0.8])
                      * float4x4(scale: Float.random(in: 0.05...0.3))
            let gray = Float.random(in: 0.35...0.65)
            rocks.append(InstanceData(model: model, color: [gray, gray * 0.95, gray * 0.88, 1]))
        }
        rockBuffer = device.makeBuffer(bytes: rocks, length: MemoryLayout<InstanceData>.stride * rocks.count,
                                       options: [])!
        rockBuffer.label = "Rock instances"

        let planet = [InstanceData(model: .identity, color: [0.6, 0.45, 0.33, 1])]
        planetBuffer = device.makeBuffer(bytes: planet, length: MemoryLayout<InstanceData>.stride, options: [])!

        let library = makeShaderLibrary(device: device, bundle: .module)
        // Both meshes use attribute 0 (position) and 1 (normal), so one pipeline per vertex layout.
        pipelineState = makePipeline(device: device, library: library,
                                     vertex: "vertex_instanced", fragment: "fragment_main",
                                     colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                     vertexDescriptor: Geometry.vertexDescriptor)
        packedPipeline = makePipeline(device: device, library: library,
                                      vertex: "vertex_instanced", fragment: "fragment_main",
                                      colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                      vertexDescriptor: Geometry.packedVertexDescriptor)
        super.init(view: view)
        view.clearColor = MTLClearColor(red: 0.01, green: 0.01, blue: 0.03, alpha: 1)
        camera.position = [0, 9, 32]
        camera.pitch = -18
        camera.speed = 12
    }

    let packedPipeline: MTLRenderPipelineState

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        encoder.setDepthStencilState(depthState)
        encoder.setFrontFacing(.counterClockwise)
        encoder.setCullMode(.back)

        var frame = FrameUniforms(view: camera.viewMatrix,
                                  projection: camera.projectionMatrix(aspect: aspect),
                                  time: 0)
        // The planet: one instance, no orbit.
        encoder.setRenderPipelineState(packedPipeline)
        encoder.setVertexValue(frame, index: 1)
        encoder.setVertexBuffer(planetBuffer, offset: 0, index: 2)
        sphere.draw(encoder)

        // The rocks: 20,000 instances in one call. The orbit is animated in the vertex function.
        frame.time = time
        encoder.setRenderPipelineState(pipelineState)
        encoder.setVertexValue(frame, index: 1)
        encoder.setVertexBuffer(rockBuffer, offset: 0, index: 2)
        cube.draw(encoder, instanceCount: rockCount)

        encoder.endEncoding()
    }
}

runApp(title: "13 Instancing (20,000 instances, one draw call)") { view in Renderer(view: view) }
