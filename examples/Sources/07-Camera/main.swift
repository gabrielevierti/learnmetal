// Chapter: Getting Started / Camera
// The ten cubes again, seen through a fly camera.
// W A S D: move, Q / E: down / up, drag with the mouse: look, scroll: zoom.

import LearnMetalKit
import MetalKit

final class Renderer: BaseRenderer {
    let pipelineState: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    let texture: MTLTexture
    let samplerState: MTLSamplerState

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        texture = Textures.crate(device: device).diffuse
        samplerState = makeSampler(device: device)
        depthState = makeDepthState(device: device)

        let library = makeShaderLibrary(device: device, bundle: .module)
        pipelineState = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_main",
                                     colorFormats: [view.colorPixelFormat],
                                     depthFormat: .depth32Float,
                                     vertexDescriptor: Geometry.vertexDescriptor)
        super.init(view: view)
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        encoder.setRenderPipelineState(pipelineState)
        encoder.setDepthStencilState(depthState)
        encoder.setFrontFacing(.counterClockwise)
        encoder.setCullMode(.back)
        encoder.setFragmentTexture(texture, index: 0)
        encoder.setFragmentSamplerState(samplerState, index: 0)

        // BaseRenderer updates `camera` from the keyboard and mouse before calling render.
        for (i, position) in Geometry.cubePositions.enumerated() {
            let model = float4x4(translation: position)
                      * float4x4(rotation: (20 * Float(i)).radians, axis: [1, 0.3, 0.5])
            encoder.setVertexValue(sceneUniforms(model: model), index: 1)
            cube.draw(encoder)
        }
        encoder.endEncoding()
    }
}

runApp(title: "07 Camera (WASD, drag, scroll)") { view in Renderer(view: view) }
