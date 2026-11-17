// Chapter: Advanced Lighting / Shadow Mapping
// Pass 1 renders depth from the light into a shadow map. Pass 2 renders the scene and
// compares each fragment's depth in light space against the map.
// Space toggles the depth bias so you can see shadow acne.

import LearnMetalKit
import MetalKit

struct ShadowUniforms {
    var model: float4x4
    var view: float4x4
    var projection: float4x4
    var normalMatrix: float3x3
    var lightViewProjection: float4x4
}

struct FragmentUniforms {
    var lightDirection: Float3      // direction the light travels
    var viewPosition: Float3
}

final class Renderer: BaseRenderer {
    let shadowPipeline: MTLRenderPipelineState
    let scenePipeline: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    let floor: SimpleMesh
    let crate: MTLTexture
    let floorTexture: MTLTexture
    let samplerState: MTLSamplerState
    let shadowSampler: MTLSamplerState
    let shadowMap: MTLTexture
    let shadowPass: MTLRenderPassDescriptor
    var useBias = true

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        floor = SimpleMesh(device: device, vertices: Geometry.plane(size: 24, uvScale: 8))
        crate = Textures.crate(device: device, sRGB: true).diffuse
        floorTexture = Textures.checker(device: device, squares: 2, sRGB: true,
                                        a: [0.55, 0.5, 0.45, 1], b: [0.4, 0.36, 0.33, 1])
        samplerState = makeSampler(device: device)
        // A comparison sampler: sample_compare returns 1 where the reference depth is <= the stored depth.
        shadowSampler = makeSampler(device: device, address: .clampToEdge, compare: .lessEqual)
        depthState = makeDepthState(device: device)

        let map = makeRenderTarget(device: device, format: .depth32Float,
                                   width: 2048, height: 2048, label: "Shadow Map")
        // No color attachment at all, and the depth must be stored: reading it is the point.
        let pass = MTLRenderPassDescriptor()
        pass.depthAttachment.texture = map
        pass.depthAttachment.loadAction = .clear
        pass.depthAttachment.clearDepth = 1
        pass.depthAttachment.storeAction = .store
        shadowMap = map
        shadowPass = pass

        let library = makeShaderLibrary(device: device, bundle: .module)
        // Depth only: no fragment function and no color attachment.
        shadowPipeline = makePipeline(device: device, library: library,
                                      vertex: "vertex_shadow", fragment: nil,
                                      colorFormats: [], depthFormat: .depth32Float,
                                      vertexDescriptor: Geometry.vertexDescriptor)
        // Linear workflow: the drawable is sRGB, so shader output is gamma-encoded automatically.
        view.colorPixelFormat = .bgra8Unorm_srgb
        scenePipeline = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_main",
                                     colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                     vertexDescriptor: Geometry.vertexDescriptor)
        super.init(view: view)
        view.clearColor = MTLClearColor(red: 0.02, green: 0.02, blue: 0.03, alpha: 1)
        camera.position = [1.5, 3.2, 7]
        camera.yaw = -100
        camera.pitch = -22
    }

    var models: [float4x4] {
        [float4x4(translation: [0, 1.5, 0]) * float4x4(rotation: time * 0.6, axis: [0.3, 1, 0.2]) * float4x4(scale: 0.5),
         float4x4(translation: [2, 0.0, 1]),
         float4x4(translation: [-1.2, 0.2, 1.8]) * float4x4(rotation: Float(60).radians, axis: [1, 0, 1]) * float4x4(scale: 0.6)]
    }

    func drawScene(_ encoder: MTLRenderCommandEncoder, lightViewProjection: float4x4) {
        func uniforms(_ model: float4x4) -> ShadowUniforms {
            ShadowUniforms(model: model, view: camera.viewMatrix,
                           projection: camera.projectionMatrix(aspect: aspect),
                           normalMatrix: model.normalMatrix,
                           lightViewProjection: lightViewProjection)
        }
        encoder.setFragmentTexture(floorTexture, index: 0)
        encoder.setVertexValue(uniforms(float4x4(translation: [0, -0.5, 0])), index: 1)
        floor.draw(encoder)

        encoder.setFragmentTexture(crate, index: 0)
        for model in models {
            encoder.setVertexValue(uniforms(model), index: 1)
            cube.draw(encoder)
        }
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        if Input.shared.wasPressed(.space) { useBias.toggle() }

        // The light's view of the scene: an orthographic box around the origin.
        let lightPosition = Float3(-3 + sin(time * 0.3) * 2, 6, -1.5)
        let lightView = float4x4(lookAt: lightPosition, center: [0.4, 0, 0.8], up: [0, 1, 0])
        let lightProjection = float4x4(orthographicLeft: -7, right: 7, bottom: -7, top: 7, near: 1, far: 16)
        let lightViewProjection = lightProjection * lightView

        // Pass 1: depth from the light.
        if let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: shadowPass) {
            encoder.label = "Shadow Pass"
            encoder.setRenderPipelineState(shadowPipeline)
            encoder.setDepthStencilState(depthState)
            if useBias {
                encoder.setDepthBias(0.015, slopeScale: 7, clamp: 0.02)
            }
            drawScene(encoder, lightViewProjection: lightViewProjection)
            encoder.endEncoding()
        }

        // Pass 2: the scene, sampling the shadow map.
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }
        encoder.label = "Main Pass"
        encoder.setRenderPipelineState(scenePipeline)
        encoder.setDepthStencilState(depthState)
        encoder.setFragmentValue(FragmentUniforms(lightDirection: normalize(Float3(0.4, 0, 0.8) - lightPosition),
                                                  viewPosition: camera.position), index: 1)
        encoder.setFragmentTexture(shadowMap, index: 1)
        encoder.setFragmentSamplerState(samplerState, index: 0)
        encoder.setFragmentSamplerState(shadowSampler, index: 1)
        drawScene(encoder, lightViewProjection: lightViewProjection)
        encoder.endEncoding()
    }
}

runApp(title: "14 Shadow Mapping (Space: toggle depth bias)") { view in Renderer(view: view) }
