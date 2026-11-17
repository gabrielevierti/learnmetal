import MetalKit
import ModelIO

/// The vertex layout used by the hand-built geometry. SIMD3 occupies 16 bytes,
/// so the offsets are 0, 16, 32 and the stride is 48.
public struct Vertex {
    public var position: Float3
    public var normal: Float3
    public var uv: SIMD2<Float>

    public init(position: Float3, normal: Float3, uv: SIMD2<Float>) {
        self.position = position
        self.normal = normal
        self.uv = uv
    }
}

/// A vertex buffer plus a vertex count, drawn as a triangle list.
public struct SimpleMesh {
    public let buffer: MTLBuffer
    public let vertexCount: Int

    public init(device: MTLDevice, vertices: [Vertex]) {
        buffer = device.makeBuffer(bytes: vertices,
                                   length: MemoryLayout<Vertex>.stride * vertices.count,
                                   options: [])!
        vertexCount = vertices.count
    }

    public func draw(_ encoder: MTLRenderCommandEncoder, instanceCount: Int = 1) {
        encoder.setVertexBuffer(buffer, offset: 0, index: 0)
        encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: vertexCount,
                               instanceCount: instanceCount)
    }
}

public enum Geometry {
    /// Ten cube positions used by several chapters.
    public static let cubePositions: [Float3] = [
        [0.0, 0.0, 0.0], [2.0, 5.0, -15.0], [-1.5, -2.2, -2.5], [-3.8, -2.0, -12.3],
        [2.4, -0.4, -3.5], [-1.7, 3.0, -7.5], [1.3, -2.0, -2.5], [1.5, 2.0, -2.5],
        [1.5, 0.2, -1.5], [-1.3, 1.0, -1.5],
    ]

    /// Vertex descriptor matching `Vertex`: position (0), normal (1), uv (2), all from buffer 0.
    public static var vertexDescriptor: MTLVertexDescriptor {
        let d = MTLVertexDescriptor()
        d.attributes[0].format = .float3
        d.attributes[0].offset = MemoryLayout<Vertex>.offset(of: \.position)!
        d.attributes[1].format = .float3
        d.attributes[1].offset = MemoryLayout<Vertex>.offset(of: \.normal)!
        d.attributes[2].format = .float2
        d.attributes[2].offset = MemoryLayout<Vertex>.offset(of: \.uv)!
        d.layouts[0].stride = MemoryLayout<Vertex>.stride
        return d
    }

    /// A unit cube centered on the origin, 36 vertices, counter-clockwise fronts.
    public static func cube() -> [Vertex] {
        let faces: [(Float3, Float3, Float3)] = [      // normal, right, up
            ([0, 0, 1], [1, 0, 0], [0, 1, 0]),
            ([0, 0, -1], [-1, 0, 0], [0, 1, 0]),
            ([1, 0, 0], [0, 0, -1], [0, 1, 0]),
            ([-1, 0, 0], [0, 0, 1], [0, 1, 0]),
            ([0, 1, 0], [1, 0, 0], [0, 0, -1]),
            ([0, -1, 0], [1, 0, 0], [0, 0, 1]),
        ]
        let corners: [SIMD2<Float>] = [[-1, -1], [1, -1], [1, 1], [-1, -1], [1, 1], [-1, 1]]
        var vertices: [Vertex] = []
        for (normal, right, up) in faces {
            for c in corners {
                let position = (normal + right * c.x + up * c.y) * 0.5
                let uv = SIMD2<Float>(c.x * 0.5 + 0.5, 0.5 - c.y * 0.5)
                vertices.append(Vertex(position: position, normal: normal, uv: uv))
            }
        }
        return vertices
    }

    /// A horizontal square in the xz plane, facing up.
    public static func plane(size: Float, uvScale: Float = 1) -> [Vertex] {
        let h = size / 2
        let up = Float3(0, 1, 0)
        let p: [Float3] = [[-h, 0, h], [h, 0, h], [h, 0, -h], [-h, 0, -h]]
        let uv: [SIMD2<Float>] = [[0, uvScale], [uvScale, uvScale], [uvScale, 0], [0, 0]]
        return [0, 1, 2, 0, 2, 3].map { Vertex(position: p[$0], normal: up, uv: uv[$0]) }
    }

    // MARK: Model I/O

    /// Tightly packed layout for Model I/O meshes: 12 + 12 + 8 = 32 bytes per vertex.
    public static var packedVertexDescriptor: MTLVertexDescriptor {
        let d = MTLVertexDescriptor()
        d.attributes[0].format = .float3
        d.attributes[0].offset = 0
        d.attributes[1].format = .float3
        d.attributes[1].offset = 12
        d.attributes[2].format = .float2
        d.attributes[2].offset = 24
        d.layouts[0].stride = 32
        return d
    }

    /// The same layout, described for Model I/O with named attributes.
    public static var modelIOVertexDescriptor: MDLVertexDescriptor {
        let d = MTKModelIOVertexDescriptorFromMetal(packedVertexDescriptor)
        (d.attributes[0] as! MDLVertexAttribute).name = MDLVertexAttributePosition
        (d.attributes[1] as! MDLVertexAttribute).name = MDLVertexAttributeNormal
        (d.attributes[2] as! MDLVertexAttribute).name = MDLVertexAttributeTextureCoordinate
        return d
    }

    public static func sphere(device: MTLDevice, radius: Float = 0.5, segments: Int = 48) -> MTKMesh {
        let allocator = MTKMeshBufferAllocator(device: device)
        let mesh = MDLMesh(sphereWithExtent: [radius, radius, radius],
                           segments: [UInt32(segments), UInt32(segments)],
                           inwardNormals: false, geometryType: .triangles, allocator: allocator)
        mesh.vertexDescriptor = modelIOVertexDescriptor
        return try! MTKMesh(mesh: mesh, device: device)
    }
}

public extension MTKMesh {
    /// Binds the vertex buffers starting at slot 0 and draws every submesh.
    func draw(_ encoder: MTLRenderCommandEncoder, instanceCount: Int = 1) {
        for (index, vertexBuffer) in vertexBuffers.enumerated() {
            encoder.setVertexBuffer(vertexBuffer.buffer, offset: vertexBuffer.offset, index: index)
        }
        for submesh in submeshes {
            encoder.drawIndexedPrimitives(type: submesh.primitiveType,
                                          indexCount: submesh.indexCount,
                                          indexType: submesh.indexType,
                                          indexBuffer: submesh.indexBuffer.buffer,
                                          indexBufferOffset: submesh.indexBuffer.offset,
                                          instanceCount: instanceCount)
        }
    }
}
