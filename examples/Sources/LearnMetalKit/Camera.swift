import simd

/// A fly camera: W A S D to move, Q and E for down and up, drag to look, scroll to zoom.
public final class Camera {
    public var position = Float3(0, 0, 3)
    public var yaw: Float = -90         // degrees; -90 looks down -z
    public var pitch: Float = 0
    public var fov: Float = 45
    public var speed: Float = 3
    public var sensitivity: Float = 0.2

    public init() {}

    public var front: Float3 {
        let y = yaw.radians, p = pitch.radians
        return normalize(Float3(cos(y) * cos(p), sin(p), sin(y) * cos(p)))
    }

    public var right: Float3 { normalize(cross(front, Float3(0, 1, 0))) }

    public var viewMatrix: float4x4 {
        float4x4(lookAt: position, center: position + front, up: Float3(0, 1, 0))
    }

    public func projectionMatrix(aspect: Float) -> float4x4 {
        float4x4(perspectiveFov: fov.radians, aspect: aspect, near: 0.1, far: 100)
    }

    /// Applies keyboard and mouse input for one frame.
    public func update(deltaTime: Float, input: Input = .shared) {
        var move = Float3(0, 0, 0)
        if input.isDown(.w) { move += front }
        if input.isDown(.s) { move -= front }
        if input.isDown(.d) { move += right }
        if input.isDown(.a) { move -= right }
        if input.isDown(.e) { move.y += 1 }
        if input.isDown(.q) { move.y -= 1 }
        position += move * speed * deltaTime

        let delta = input.takeMouseDelta()
        yaw += delta.x * sensitivity
        pitch = min(max(pitch - delta.y * sensitivity, -89), 89)

        fov = min(max(fov - input.takeScroll() * 0.5, 10), 70)
    }
}
