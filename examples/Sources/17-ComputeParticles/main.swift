// Chapters: Beyond / Compute Shaders, Advanced Metal / Life Without Geometry Shaders
// A compute kernel moves 200,000 particles around an attractor. A render pass then draws
// them as camera-facing quads built in the vertex function, with additive blending.
// The particle buffer never leaves the GPU.

import LearnMetalKit
import MetalKit

struct Particle {
    var position: Float3
    var velocity: Float3
    var life: Float
}

struct SimulationUniforms {
    var attractor: Float3
    var deltaTime: Float
    var particleCount: UInt32
}

struct DrawUniforms {
    var view: float4x4
    var projection: float4x4
    var size: Float
}

final class Renderer: BaseRenderer {
    let computePipeline: MTLComputePipelineState
    let renderPipeline: MTLRenderPipelineState
    let particleBuffer: MTLBuffer
    let particleCount = 200_000

    init(view: MTKView) {
        let device = view.device!

        var particles: [Particle] = []
        particles.reserveCapacity(particleCount)
        for _ in 0..<particleCount {
            let direction = normalize(Float3(.random(in: -1...1), .random(in: -0.3...0.3), .random(in: -1...1)))
            let position = direction * Float.random(in: 1.5...4.5)
            // Start with a velocity roughly perpendicular to the position, so the particles orbit.
            let tangent = normalize(cross(position, Float3(0, 1, 0)))
            particles.append(Particle(position: position,
                                      velocity: tangent * Float.random(in: 0.8...1.6),
                                      life: .random(in: 0...1)))
        }
        particleBuffer = device.makeBuffer(bytes: particles,
                                           length: MemoryLayout<Particle>.stride * particleCount,
                                           options: [])!
        particleBuffer.label = "Particles"

        let library = makeShaderLibrary(device: device, bundle: .module)
        do {
            computePipeline = try device.makeComputePipelineState(function: library.makeFunction(name: "update_particles")!)
        } catch {
            fatalError("Could not create compute pipeline: \(error)")
        }
        renderPipeline = makePipeline(device: device, library: library,
                                      vertex: "vertex_particle", fragment: "fragment_particle",
                                      colorFormats: [view.colorPixelFormat],
                                      blending: .additive)
        super.init(view: view, depth: false)
        view.clearColor = MTLClearColor(red: 0.01, green: 0.01, blue: 0.02, alpha: 1)
        camera.position = [0, 3, 9]
        camera.pitch = -18
        camera.speed = 6
    }

    override func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {
        // Compute pass: one thread per particle.
        if let compute = commandBuffer.makeComputeCommandEncoder() {
            compute.label = "Update Particles"
            compute.setComputePipelineState(computePipeline)
            compute.setBuffer(particleBuffer, offset: 0, index: 0)
            var simulation = SimulationUniforms(attractor: [sin(time * 0.5) * 1.5, 0, cos(time * 0.4) * 1.5],
                                                deltaTime: deltaTime,
                                                particleCount: UInt32(particleCount))
            compute.setBytes(&simulation, length: MemoryLayout<SimulationUniforms>.stride, index: 1)

            // Uniform threadgroups work on every device; the kernel checks the particle count itself.
            let groupSize = computePipeline.threadExecutionWidth
            let groupCount = (particleCount + groupSize - 1) / groupSize
            compute.dispatchThreadgroups(MTLSize(width: groupCount, height: 1, depth: 1),
                                         threadsPerThreadgroup: MTLSize(width: groupSize, height: 1, depth: 1))
            compute.endEncoding()
        }

        // Render pass: four vertices per instance, one instance per particle.
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else { return }
        encoder.label = "Draw Particles"
        encoder.setRenderPipelineState(renderPipeline)
        encoder.setVertexBuffer(particleBuffer, offset: 0, index: 0)
        encoder.setVertexValue(DrawUniforms(view: camera.viewMatrix,
                                            projection: camera.projectionMatrix(aspect: aspect),
                                            size: 0.035), index: 1)
        encoder.drawPrimitives(type: .triangleStrip, vertexStart: 0, vertexCount: 4,
                               instanceCount: particleCount)
        encoder.endEncoding()
    }
}

runApp(title: "17 Compute Particles (200,000 particles)") { view in Renderer(view: view) }
