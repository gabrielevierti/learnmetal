// Chapters: PBR / Theory, Lighting
// A grid of spheres shaded with the Cook-Torrance BRDF and four point lights.
// Metalness increases from bottom to top, roughness from left to right.

import LearnMetalKit
import MetalKit

struct PBRUniforms {
    var viewPosition: Float3
    var albedo: Float3
    var metallic: Float
    var roughness: Float
    var ao: Float
    var lightCount: UInt32
}

struct PBRLight {
    var position: Float3
    var color: Float3
}

final class Renderer: BaseRenderer {
    let pipelineState: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let sphere: MTKMesh
    let lightBuffer: MTLBuffer
    let lightCount: Int

    init(view: MTKView) {
        let device = view.device!
        sphere = Geometry.sphere(device: device, radius: 0.5, segments: 64)
        depthState = makeDepthState(device: device)

        // With inverse-square falloff, light colors are radiant intensities far above 1.
        let lights: [PBRLight] = [
            PBRLight(position: [-10, 10, 10], color: [300, 300, 300]),
            PBRLight(position: [10, 10, 10], color: [300, 300, 300]),
            PBRLight(position: [-10, -10, 10], color: [300, 300, 300]),
            PBRLight(position: [10, -10, 10], color: [300, 300, 300]),
        ]
        lightCount = lights.count
        lightBuffer = device.makeBuffer(bytes: lights, length: MemoryLayout<PBRLight>.stride * lights.count,
                                        options: [])!

        // PBR needs a linear workflow: an sRGB drawable gamma-encodes the shader's linear output.
        view.colorPixelFormat = .bgra8Unorm_srgb
        let library = makeShaderLibrary(device: device, bundle: .module)
        pipelineState = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_pbr",
                                     colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                     vertexDescriptor: Geometry.packedVertexDescriptor)
        super.init(view: view)
        view.clearColor = MTLClearColor(red: 0.01, green: 0.01, blue: 0.01, alpha: 1)
        camera.position = [0, 0, 14]
        camera.fov = 40
        camera.speed = 6
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        encoder.setRenderPipelineState(pipelineState)
        encoder.setDepthStencilState(depthState)
        encoder.setFragmentBuffer(lightBuffer, offset: 0, index: 2)

        let rows = 7, columns = 7
        var uniforms = PBRUniforms(viewPosition: camera.position, albedo: [0.5, 0.0, 0.0],
                                   metallic: 0, roughness: 0, ao: 1, lightCount: UInt32(lightCount))
        for row in 0..<rows {
            uniforms.metallic = Float(row) / Float(rows - 1)
            for column in 0..<columns {
                // A roughness of exactly 0 gives an infinitely small highlight, so clamp it.
                uniforms.roughness = max(Float(column) / Float(columns - 1), 0.05)
                let position = Float3(Float(column - columns / 2) * 1.25, Float(row - rows / 2) * 1.25, 0)
                encoder.setVertexValue(sceneUniforms(model: float4x4(translation: position)), index: 1)
                encoder.setFragmentValue(uniforms, index: 1)
                sphere.draw(encoder)
            }
        }
        encoder.endEncoding()
    }
}

runApp(title: "16 PBR (metalness: bottom to top, roughness: left to right)") { view in Renderer(view: view) }
