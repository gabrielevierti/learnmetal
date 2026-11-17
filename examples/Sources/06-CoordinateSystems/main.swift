// Chapter: Getting Started / Coordinate Systems
// Ten textured cubes with a model, view and projection matrix and a depth buffer.
// Press Space to turn the depth test off and see why it is needed.

import LearnMetalKit
import MetalKit

final class Renderer: BaseRenderer {
    let pipelineState: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let noDepthState: MTLDepthStencilState
    let cube: SimpleMesh
    let texture: MTLTexture
    let samplerState: MTLSamplerState
    var depthTestEnabled = true

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        texture = Textures.crate(device: device).diffuse
        samplerState = makeSampler(device: device)
        depthState = makeDepthState(device: device, compare: .less, write: true)
        noDepthState = makeDepthState(device: device, compare: .always, write: false)

        let library = makeShaderLibrary(device: device, bundle: .module)
        pipelineState = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_main",
                                     colorFormats: [view.colorPixelFormat],
                                     depthFormat: .depth32Float,
                                     vertexDescriptor: Geometry.vertexDescriptor)
        super.init(view: view)
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        if Input.shared.wasPressed(.space) { depthTestEnabled.toggle() }

        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        encoder.setRenderPipelineState(pipelineState)
        encoder.setDepthStencilState(depthTestEnabled ? depthState : noDepthState)
        encoder.setFragmentTexture(texture, index: 0)
        encoder.setFragmentSamplerState(samplerState, index: 0)

        // A fixed camera: the world is moved 3 units away from it. (The fly camera comes next.)
        let viewMatrix = float4x4(translation: [0, 0, -3])
        let projection = float4x4(perspectiveFov: Float(45).radians, aspect: aspect, near: 0.1, far: 100)

        for (i, position) in Geometry.cubePositions.enumerated() {
            var angle = (20 * Float(i)).radians
            if i % 3 == 0 { angle += time }
            let model = float4x4(translation: position) * float4x4(rotation: angle, axis: [1, 0.3, 0.5])
            encoder.setVertexValue(SceneUniforms(model: model, view: viewMatrix, projection: projection), index: 1)
            cube.draw(encoder)
        }
        encoder.endEncoding()
    }
}

runApp(title: "06 Coordinate Systems (Space: toggle depth test)") { view in Renderer(view: view) }
