// Chapter: Lighting / Lighting Maps
// A crate whose color comes from a diffuse map and whose shininess comes from a specular map.
// Hold Space to ignore the specular map and see the difference.

import LearnMetalKit
import MetalKit

struct FragmentUniforms {
    var lightPosition: Float3
    var viewPosition: Float3
    var shininess: Float
    var useSpecularMap: UInt32
}

final class Renderer: BaseRenderer {
    let litPipeline: MTLRenderPipelineState
    let lampPipeline: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    let diffuseMap: MTLTexture
    let specularMap: MTLTexture
    let samplerState: MTLSamplerState

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        depthState = makeDepthState(device: device)
        let crate = Textures.crate(device: device)
        diffuseMap = crate.diffuse
        specularMap = crate.specular
        samplerState = makeSampler(device: device)

        let library = makeShaderLibrary(device: device, bundle: .module)
        litPipeline = makePipeline(device: device, library: library,
                                   vertex: "vertex_main", fragment: "fragment_main",
                                   colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                   vertexDescriptor: Geometry.vertexDescriptor)
        lampPipeline = makePipeline(device: device, library: library,
                                    vertex: "vertex_main", fragment: "fragment_lamp",
                                    colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                    vertexDescriptor: Geometry.vertexDescriptor)
        super.init(view: view)
        view.clearColor = MTLClearColor(red: 0.1, green: 0.1, blue: 0.1, alpha: 1)
        camera.position = [-1.2, 1.0, 2.6]
        camera.yaw = -65
        camera.pitch = -18
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        let lightPosition = Float3(cos(time * 0.8) * 1.6, 0.8, sin(time * 0.8) * 1.6)
        let fragmentUniforms = FragmentUniforms(lightPosition: lightPosition,
                                                viewPosition: camera.position,
                                                shininess: 64,
                                                useSpecularMap: Input.shared.isDown(.space) ? 0 : 1)

        encoder.setDepthStencilState(depthState)
        encoder.setFrontFacing(.counterClockwise)
        encoder.setCullMode(.back)

        encoder.setRenderPipelineState(litPipeline)
        encoder.setVertexValue(sceneUniforms(model: .identity), index: 1)
        encoder.setFragmentValue(fragmentUniforms, index: 1)
        encoder.setFragmentTexture(diffuseMap, index: 0)
        encoder.setFragmentTexture(specularMap, index: 1)
        encoder.setFragmentSamplerState(samplerState, index: 0)
        cube.draw(encoder)

        encoder.setRenderPipelineState(lampPipeline)
        encoder.setVertexValue(sceneUniforms(model: float4x4(translation: lightPosition) * float4x4(scale: 0.15)),
                               index: 1)
        cube.draw(encoder)

        encoder.endEncoding()
    }
}

runApp(title: "09 Lighting Maps (hold Space: no specular map)") { view in Renderer(view: view) }
