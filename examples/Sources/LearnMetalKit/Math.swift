import simd

public typealias Float3 = SIMD3<Float>

public extension Float {
    /// Degrees to radians.
    var radians: Float { self * .pi / 180 }
}

public extension float4x4 {
    static let identity = matrix_identity_float4x4

    init(translation t: Float3) {
        self = .identity
        columns.3 = SIMD4<Float>(t, 1)
    }

    init(scale s: Float3) {
        self.init(diagonal: SIMD4<Float>(s, 1))
    }

    init(scale s: Float) {
        self.init(diagonal: SIMD4<Float>(s, s, s, 1))
    }

    init(rotation angle: Float, axis: Float3) {
        self.init(simd_quatf(angle: angle, axis: normalize(axis)))
    }

    /// Right-handed perspective projection with Metal's 0...1 depth range.
    init(perspectiveFov fovY: Float, aspect: Float, near: Float, far: Float) {
        let y = 1 / tan(fovY * 0.5)
        let x = y / aspect
        let z = far / (near - far)
        self.init(columns: (
            SIMD4<Float>(x, 0, 0, 0),
            SIMD4<Float>(0, y, 0, 0),
            SIMD4<Float>(0, 0, z, -1),
            SIMD4<Float>(0, 0, z * near, 0)))
    }

    /// Right-handed orthographic projection with Metal's 0...1 depth range.
    init(orthographicLeft l: Float, right r: Float, bottom b: Float, top t: Float, near n: Float, far f: Float) {
        self.init(columns: (
            SIMD4<Float>(2 / (r - l), 0, 0, 0),
            SIMD4<Float>(0, 2 / (t - b), 0, 0),
            SIMD4<Float>(0, 0, 1 / (n - f), 0),
            SIMD4<Float>((l + r) / (l - r), (t + b) / (b - t), n / (n - f), 1)))
    }

    /// Right-handed view matrix.
    init(lookAt eye: Float3, center: Float3, up: Float3) {
        let z = normalize(eye - center)
        let x = normalize(cross(up, z))
        let y = cross(z, x)
        self.init(columns: (
            SIMD4<Float>(x.x, y.x, z.x, 0),
            SIMD4<Float>(x.y, y.y, z.y, 0),
            SIMD4<Float>(x.z, y.z, z.z, 0),
            SIMD4<Float>(-dot(x, eye), -dot(y, eye), -dot(z, eye), 1)))
    }

    /// Rotation and scale without translation.
    var upperLeft: float3x3 {
        float3x3(SIMD3(columns.0.x, columns.0.y, columns.0.z),
                 SIMD3(columns.1.x, columns.1.y, columns.1.z),
                 SIMD3(columns.2.x, columns.2.y, columns.2.z))
    }

    /// The matrix to transform normals with: inverse transpose of the upper-left 3x3.
    var normalMatrix: float3x3 { upperLeft.inverse.transpose }
}
