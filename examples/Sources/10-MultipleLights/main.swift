// Chapters: Lighting / Light Casters, Multiple Lights
// Ten crates lit by a directional light, four colored point lights stored in a buffer,
// and a flashlight (spotlight) attached to the camera. Press Space to toggle the flashlight.

import LearnMetalKit
import MetalKit

struct PointLight {
    var position: Float3
    var color: Float3
}

struct FragmentUniforms {
    var viewPosition: Float3
    var sunDirection: Float3
    var sunColor: Float3
    var spotPosition: Float3
    var spotDirection: Float3
    var spotCutoff: SIMD2<Float>        // cosines of the inner and outer angle
    var pointLightCount: UInt32
    var spotEnabled: UInt32
}

final class Renderer: BaseRenderer {
    let litPipeline: MTLRenderPipelineState
    let lampPipeline: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    let diffuseMap: MTLTexture
    let specularMap: MTLTexture
    let samplerState: MTLSamplerState
    let lightBuffer: MTLBuffer
    var flashlight = true

    let pointLights: [PointLight] = [
        PointLight(position: [0.7, 0.2, 2.0], color: [1.0, 0.6, 0.3]),
        PointLight(position: [2.3, -3.3, -4.0], color: [0.4, 0.6, 1.0]),
        PointLight(position: [-4.0, 2.0, -12.0], color: [0.5, 1.0, 0.5]),
        PointLight(position: [0.0, 0.0, -3.0], color: [1.0, 0.4, 0.5]),
    ]

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        depthState = makeDepthState(device: device)
        let crate = Textures.crate(device: device)
        diffuseMap = crate.diffuse
        specularMap = crate.specular
        samplerState = makeSampler(device: device)

        // Lights that come in variable numbers live in their own buffer.
        lightBuffer = device.makeBuffer(bytes: pointLights,
                                        length: MemoryLayout<PointLight>.stride * pointLights.count,
                                        options: [])!
        lightBuffer.label = "Point lights"

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
        view.clearColor = MTLClearColor(red: 0.04, green: 0.04, blue: 0.06, alpha: 1)
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        if Input.shared.wasPressed(.space) { flashlight.toggle() }

        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        let fragmentUniforms = FragmentUniforms(
            viewPosition: camera.position,
            sunDirection: [-0.2, -1.0, -0.3],
            sunColor: [0.35, 0.35, 0.4],
            spotPosition: camera.position,
            spotDirection: camera.front,
            spotCutoff: [cos(Float(12.5).radians), cos(Float(17.5).radians)],
            pointLightCount: UInt32(pointLights.count),
            spotEnabled: flashlight ? 1 : 0)

        encoder.setDepthStencilState(depthState)
        encoder.setFrontFacing(.counterClockwise)
        encoder.setCullMode(.back)

        encoder.setRenderPipelineState(litPipeline)
        encoder.setFragmentValue(fragmentUniforms, index: 1)
        encoder.setFragmentBuffer(lightBuffer, offset: 0, index: 2)
        encoder.setFragmentTexture(diffuseMap, index: 0)
        encoder.setFragmentTexture(specularMap, index: 1)
        encoder.setFragmentSamplerState(samplerState, index: 0)
        for (i, position) in Geometry.cubePositions.enumerated() {
            let model = float4x4(translation: position)
                      * float4x4(rotation: (20 * Float(i)).radians, axis: [1, 0.3, 0.5])
            encoder.setVertexValue(sceneUniforms(model: model), index: 1)
            cube.draw(encoder)
        }

        encoder.setRenderPipelineState(lampPipeline)
        for light in pointLights {
            encoder.setVertexValue(sceneUniforms(model: float4x4(translation: light.position) * float4x4(scale: 0.15)),
                                   index: 1)
            encoder.setFragmentValue(light.color, index: 1)
            cube.draw(encoder)
        }

        encoder.endEncoding()
    }
}

runApp(title: "10 Multiple Lights (Space: flashlight, WASD + drag: camera)") { view in Renderer(view: view) }
