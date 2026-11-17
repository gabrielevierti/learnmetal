// Chapters: Lighting / Colors, Basic Lighting, Materials
// A coral cube lit by one orbiting light with the Phong model: ambient + diffuse + specular.
// Keys 1 to 4 switch between materials.

import LearnMetalKit
import MetalKit

struct Material {
    var ambient: Float3
    var diffuse: Float3
    var specular: Float3
    var shininess: Float
}

struct Light {
    var position: Float3
    var ambient: Float3
    var diffuse: Float3
    var specular: Float3
}

struct FragmentUniforms {
    var material: Material
    var light: Light
    var viewPosition: Float3
}

let materials: [Material] = [
    Material(ambient: [1.0, 0.5, 0.31], diffuse: [1.0, 0.5, 0.31], specular: [0.5, 0.5, 0.5], shininess: 32),          // coral
    Material(ambient: [0.02, 0.17, 0.02], diffuse: [0.08, 0.61, 0.08], specular: [0.63, 0.73, 0.63], shininess: 77),   // emerald
    Material(ambient: [0.25, 0.20, 0.07], diffuse: [0.75, 0.61, 0.23], specular: [0.63, 0.56, 0.37], shininess: 51),   // gold
    Material(ambient: [0.0, 0.1, 0.06], diffuse: [0.0, 0.51, 0.51], specular: [0.5, 0.5, 0.5], shininess: 32),         // cyan plastic
]

final class Renderer: BaseRenderer {
    let litPipeline: MTLRenderPipelineState
    let lampPipeline: MTLRenderPipelineState
    let depthState: MTLDepthStencilState
    let cube: SimpleMesh
    var materialIndex = 0

    init(view: MTKView) {
        let device = view.device!
        cube = SimpleMesh(device: device, vertices: Geometry.cube())
        depthState = makeDepthState(device: device)

        let library = makeShaderLibrary(device: device, bundle: .module)
        litPipeline = makePipeline(device: device, library: library,
                                   vertex: "vertex_main", fragment: "fragment_main",
                                   colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                   vertexDescriptor: Geometry.vertexDescriptor)
        // Same vertex function, different fragment function: a second pipeline state.
        lampPipeline = makePipeline(device: device, library: library,
                                    vertex: "vertex_main", fragment: "fragment_lamp",
                                    colorFormats: [view.colorPixelFormat], depthFormat: .depth32Float,
                                    vertexDescriptor: Geometry.vertexDescriptor)
        super.init(view: view)
        view.clearColor = MTLClearColor(red: 0.1, green: 0.1, blue: 0.1, alpha: 1)
        camera.position = [-1.5, 1.2, 3.5]
        camera.yaw = -65
        camera.pitch = -15
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        for (index, key) in [Key.one, .two, .three, .four].enumerated() where Input.shared.wasPressed(key) {
            materialIndex = index
        }

        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }

        let lightPosition = Float3(cos(time) * 2, 1.0, sin(time) * 2)
        let fragmentUniforms = FragmentUniforms(
            material: materials[materialIndex],
            light: Light(position: lightPosition, ambient: [0.2, 0.2, 0.2], diffuse: [0.8, 0.8, 0.8], specular: [1, 1, 1]),
            viewPosition: camera.position)

        encoder.setDepthStencilState(depthState)
        encoder.setFrontFacing(.counterClockwise)
        encoder.setCullMode(.back)

        // The object
        encoder.setRenderPipelineState(litPipeline)
        encoder.setVertexValue(sceneUniforms(model: .identity), index: 1)
        encoder.setFragmentValue(fragmentUniforms, index: 1)
        cube.draw(encoder)

        // The lamp: a small unlit cube at the light's position
        encoder.setRenderPipelineState(lampPipeline)
        let lampModel = float4x4(translation: lightPosition) * float4x4(scale: 0.2)
        encoder.setVertexValue(sceneUniforms(model: lampModel), index: 1)
        cube.draw(encoder)

        encoder.endEncoding()
    }
}

runApp(title: "08 Basic Lighting (1-4: material, WASD + drag: camera)") { view in Renderer(view: view) }
