// Chapter: Advanced Metal / Render Targets
// Pass 1 draws the scene into a texture. Pass 2 draws that texture to the screen with a
// full-screen triangle and a post-processing effect.
// Keys: 1 none, 2 inverted, 3 grayscale, 4 edge detection.

import LearnMetalKit
import MetalKit

final class Renderer: BaseRenderer {
    let scenePipeline: MTLRenderPipelineState
    let postPipeline: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    let texture: MTLTexture
    let repeatSampler: MTLSamplerState
    let clampSampler: MTLSamplerState

    var sceneColor: MTLTexture?
    var sceneDepth: MTLTexture?
    var effect: UInt32 = 0

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        texture = Textures.crate(device: device).diffuse
        repeatSampler = makeSampler(device: device, address: .repeat)
        clampSampler = makeSampler(device: device, address: .clampToEdge)
        depthState = makeDepthState(device: device)

        let library = makeShaderLibrary(device: device, bundle: .module)
        // The scene pipeline targets our offscreen textures...
        scenePipeline = makePipeline(device: device, library: library,
                                     vertex: "vertex_main", fragment: "fragment_main",
                                     colorFormats: [.bgra8Unorm], depthFormat: .depth32Float,
                                     vertexDescriptor: Geometry.vertexDescriptor)
        // ...and the post pipeline targets the drawable. It has no vertex descriptor and no depth.
        postPipeline = makePipeline(device: device, library: library,
                                    vertex: "vertex_fullscreen", fragment: "fragment_post",
                                    colorFormats: [view.colorPixelFormat])
        super.init(view: view, depth: false)
    }

    func makeTargetsIfNeeded(size: CGSize) {
        let width = Int(size.width), height = Int(size.height)
        if let color = sceneColor, color.width == width, color.height == height { return }

        sceneColor = makeRenderTarget(device: device, format: .bgra8Unorm,
                                      width: width, height: height, label: "Scene Color")
        sceneDepth = makeRenderTarget(device: device, format: .depth32Float,
                                      width: width, height: height, label: "Scene Depth")
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        for (index, key) in [Key.one, .two, .three, .four].enumerated() where Input.shared.wasPressed(key) {
            effect = UInt32(index)
        }
        makeTargetsIfNeeded(size: view.drawableSize)

        // Pass 1: the scene, into our texture.
        let scenePass = MTLRenderPassDescriptor()
        scenePass.colorAttachments[0].texture = sceneColor
        scenePass.colorAttachments[0].loadAction = .clear
        scenePass.colorAttachments[0].clearColor = MTLClearColor(red: 0.2, green: 0.3, blue: 0.3, alpha: 1)
        scenePass.colorAttachments[0].storeAction = .store        // needed by pass 2
        scenePass.depthAttachment.texture = sceneDepth
        scenePass.depthAttachment.loadAction = .clear
        scenePass.depthAttachment.clearDepth = 1
        scenePass.depthAttachment.storeAction = .dontCare         // only needed during this pass

        if let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: scenePass) {
            encoder.label = "Scene Pass"
            encoder.setRenderPipelineState(scenePipeline)
            encoder.setDepthStencilState(depthState)
            encoder.setFrontFacing(.counterClockwise)
            encoder.setCullMode(.back)
            encoder.setFragmentTexture(texture, index: 0)
            encoder.setFragmentSamplerState(repeatSampler, index: 0)
            for (i, position) in Geometry.cubePositions.enumerated() {
                let model = float4x4(translation: position)
                          * float4x4(rotation: (20 * Float(i)).radians + time * 0.3, axis: [1, 0.3, 0.5])
                encoder.setVertexValue(sceneUniforms(model: model), index: 1)
                cube.draw(encoder)
            }
            encoder.endEncoding()
        }

        // Pass 2: a full-screen triangle, into the drawable.
        guard let viewPass = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: viewPass) else { return }
        encoder.label = "Post-Processing Pass"
        encoder.setRenderPipelineState(postPipeline)
        encoder.setFragmentTexture(sceneColor, index: 0)
        encoder.setFragmentSamplerState(clampSampler, index: 0)
        encoder.setFragmentValue(effect, index: 0)
        encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
        encoder.endEncoding()
    }
}

runApp(title: "12 Render Targets (1-4: effect)") { view in Renderer(view: view) }
