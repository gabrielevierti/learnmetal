// Chapters: Advanced Lighting / HDR, Bloom
// The scene is rendered into a floating-point texture with a second attachment that keeps
// only the bright parts. Those are blurred at half resolution, added back, and tone mapped.
// Space: toggle bloom. W / S move the camera as usual; 1 / 2 lower / raise the exposure.

import LearnMetalKit
import MetalKit

struct PointLight {
    var position: Float3
    var color: Float3
}

struct FragmentUniforms {
    var viewPosition: Float3
    var lightCount: UInt32
}

struct CompositeUniforms {
    var exposure: Float
    var bloomStrength: Float
}

final class Renderer: BaseRenderer {
    let scenePipeline: MTLRenderPipelineState
    let lampPipeline: MTLRenderPipelineState
    let blurPipeline: MTLRenderPipelineState
    let compositePipeline: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    let floor: SimpleMesh
    let crate: MTLTexture
    let floorTexture: MTLTexture
    let repeatSampler: MTLSamplerState
    let clampSampler: MTLSamplerState
    let lightBuffer: MTLBuffer

    var hdrColor: MTLTexture?
    var brightColor: MTLTexture?
    var sceneDepth: MTLTexture?
    var blurA: MTLTexture?
    var blurB: MTLTexture?

    var bloomEnabled = true
    var exposure: Float = 1.0

    let lights: [PointLight] = [
        PointLight(position: [-2.4, 0.3, 0.2], color: [5.0, 1.2, 0.7]),
        PointLight(position: [2.6, 0.5, -0.6], color: [1.0, 2.5, 5.0]),
        PointLight(position: [0.4, 0.2, 1.4], color: [1.5, 5.0, 2.0]),
        PointLight(position: [0.2, 1.8, -2.2], color: [5.0, 4.0, 1.5]),
    ]

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        floor = SimpleMesh(device: device, vertices: Geometry.plane(size: 24, uvScale: 8))
        crate = Textures.crate(device: device, sRGB: true).diffuse
        floorTexture = Textures.checker(device: device, squares: 2, sRGB: true,
                                        a: [0.5, 0.45, 0.4, 1], b: [0.36, 0.33, 0.3, 1])
        repeatSampler = makeSampler(device: device, address: .repeat)
        clampSampler = makeSampler(device: device, address: .clampToEdge)
        depthState = makeDepthState(device: device)
        lightBuffer = device.makeBuffer(bytes: lights, length: MemoryLayout<PointLight>.stride * lights.count,
                                        options: [])!

        let library = makeShaderLibrary(device: device, bundle: .module)
        let hdr: [MTLPixelFormat] = [.rgba16Float, .rgba16Float]     // color, bright parts
        scenePipeline = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_main",
                                     colorFormats: hdr, depthFormat: .depth32Float,
                                     vertexDescriptor: Geometry.vertexDescriptor)
        lampPipeline = makePipeline(device: device, library: library,
                                    vertex: "vertex_main", fragment: "fragment_lamp",
                                    colorFormats: hdr, depthFormat: .depth32Float,
                                    vertexDescriptor: Geometry.vertexDescriptor)
        blurPipeline = makePipeline(device: device, library: library,
                                    vertex: "vertex_fullscreen", fragment: "fragment_blur",
                                    colorFormats: [.rgba16Float])
        view.colorPixelFormat = .bgra8Unorm_srgb
        compositePipeline = makePipeline(device: device, library: library,
                                         vertex: "vertex_fullscreen", fragment: "fragment_composite",
                                         colorFormats: [view.colorPixelFormat])
        super.init(view: view, depth: false)
        camera.position = [0.3, 1.6, 5.2]
        camera.pitch = -14
    }

    func makeTargetsIfNeeded(size: CGSize) {
        let width = Int(size.width), height = Int(size.height)
        if let color = hdrColor, color.width == width, color.height == height { return }
        hdrColor = makeRenderTarget(device: device, format: .rgba16Float, width: width, height: height, label: "HDR Color")
        brightColor = makeRenderTarget(device: device, format: .rgba16Float, width: width, height: height, label: "Bright Parts")
        sceneDepth = makeRenderTarget(device: device, format: .depth32Float, width: width, height: height, label: "Depth")
        blurA = makeRenderTarget(device: device, format: .rgba16Float, width: width / 2, height: height / 2, label: "Blur A")
        blurB = makeRenderTarget(device: device, format: .rgba16Float, width: width / 2, height: height / 2, label: "Blur B")
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        if Input.shared.wasPressed(.space) { bloomEnabled.toggle() }
        if Input.shared.wasPressed(.one) { exposure = max(exposure * 0.8, 0.1) }
        if Input.shared.wasPressed(.two) { exposure = min(exposure * 1.25, 8) }
        makeTargetsIfNeeded(size: view.drawableSize)

        // Pass 1: the scene in HDR, writing two color attachments at once.
        let scenePass = MTLRenderPassDescriptor()
        for (index, texture) in [hdrColor, brightColor].enumerated() {
            scenePass.colorAttachments[index].texture = texture
            scenePass.colorAttachments[index].loadAction = .clear
            scenePass.colorAttachments[index].clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
            scenePass.colorAttachments[index].storeAction = .store
        }
        scenePass.depthAttachment.texture = sceneDepth
        scenePass.depthAttachment.loadAction = .clear
        scenePass.depthAttachment.clearDepth = 1
        scenePass.depthAttachment.storeAction = .dontCare

        if let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: scenePass) {
            encoder.label = "HDR Scene Pass"
            encoder.setDepthStencilState(depthState)
            encoder.setRenderPipelineState(scenePipeline)
            encoder.setFragmentValue(FragmentUniforms(viewPosition: camera.position,
                                                      lightCount: UInt32(lights.count)), index: 1)
            encoder.setFragmentBuffer(lightBuffer, offset: 0, index: 2)
            encoder.setFragmentSamplerState(repeatSampler, index: 0)

            encoder.setFragmentTexture(floorTexture, index: 0)
            encoder.setVertexValue(sceneUniforms(model: float4x4(translation: [0, -0.5, 0])), index: 1)
            floor.draw(encoder)

            encoder.setFragmentTexture(crate, index: 0)
            let crates: [float4x4] = [
                float4x4(translation: [-1.0, 0, -1.2]) * float4x4(rotation: Float(25).radians, axis: [0, 1, 0]),
                float4x4(translation: [1.4, 0, -0.2]) * float4x4(rotation: Float(-15).radians, axis: [0, 1, 0]),
                float4x4(translation: [0.2, 0.8, -1.0]) * float4x4(rotation: time * 0.5, axis: [0, 1, 0]) * float4x4(scale: 0.6),
            ]
            for model in crates {
                encoder.setVertexValue(sceneUniforms(model: model), index: 1)
                cube.draw(encoder)
            }

            // The lamps are emissive: their color goes far above 1.0, which is what makes them bloom.
            encoder.setRenderPipelineState(lampPipeline)
            for light in lights {
                encoder.setVertexValue(sceneUniforms(model: float4x4(translation: light.position) * float4x4(scale: 0.2)),
                                       index: 1)
                encoder.setFragmentValue(light.color * 2, index: 1)
                cube.draw(encoder)
            }
            encoder.endEncoding()
        }

        // Passes 2...n: separable Gaussian blur, alternating between two half-size textures.
        var source = brightColor
        if bloomEnabled {
            for i in 0..<8 {
                let horizontal = i % 2 == 0
                let target = horizontal ? blurA : blurB
                let pass = MTLRenderPassDescriptor()
                pass.colorAttachments[0].texture = target
                pass.colorAttachments[0].loadAction = .dontCare      // every pixel is overwritten
                pass.colorAttachments[0].storeAction = .store
                guard let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: pass) else { continue }
                encoder.label = horizontal ? "Blur Horizontal" : "Blur Vertical"
                encoder.setRenderPipelineState(blurPipeline)
                encoder.setFragmentValue(horizontal ? SIMD2<Float>(1, 0) : SIMD2<Float>(0, 1), index: 0)
                encoder.setFragmentTexture(source, index: 0)
                encoder.setFragmentSamplerState(clampSampler, index: 0)
                encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
                encoder.endEncoding()
                source = target
            }
        }

        // Final pass: add the glow, tone map, and write to the sRGB drawable.
        guard let viewPass = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: viewPass) else { return }
        encoder.label = "Composite Pass"
        encoder.setRenderPipelineState(compositePipeline)
        encoder.setFragmentValue(CompositeUniforms(exposure: exposure, bloomStrength: bloomEnabled ? 1 : 0), index: 0)
        encoder.setFragmentTexture(hdrColor, index: 0)
        encoder.setFragmentTexture(source, index: 1)
        encoder.setFragmentSamplerState(clampSampler, index: 0)
        encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
        encoder.endEncoding()
    }
}

runApp(title: "15 HDR + Bloom (Space: bloom, 1 / 2: exposure)") { view in Renderer(view: view) }
