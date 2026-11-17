import Metal
import simd

/// Procedural textures, so the examples run without any image files.
/// To use your own images, load them with MTKTextureLoader as the Textures chapter shows.
public enum Textures {
    /// Builds an RGBA texture by calling `pixel` for every texel. u and v run from 0 to 1, v downward.
    public static func make(device: MTLDevice, size: Int = 256, sRGB: Bool = false,
                            pixel: (_ u: Float, _ v: Float) -> SIMD4<Float>) -> MTLTexture {
        var bytes = [UInt8](repeating: 0, count: size * size * 4)
        for y in 0..<size {
            for x in 0..<size {
                let c = simd_clamp(pixel((Float(x) + 0.5) / Float(size), (Float(y) + 0.5) / Float(size)),
                                   SIMD4<Float>(repeating: 0), SIMD4<Float>(repeating: 1)) * 255
                let i = (y * size + x) * 4
                bytes[i] = UInt8(c.x)
                bytes[i + 1] = UInt8(c.y)
                bytes[i + 2] = UInt8(c.z)
                bytes[i + 3] = UInt8(c.w)
            }
        }
        let descriptor = MTLTextureDescriptor.texture2DDescriptor(
            pixelFormat: sRGB ? .rgba8Unorm_srgb : .rgba8Unorm, width: size, height: size, mipmapped: true)
        descriptor.usage = [.shaderRead, .renderTarget]     // renderTarget is needed to generate mipmaps
        let texture = device.makeTexture(descriptor: descriptor)!
        texture.replace(region: MTLRegionMake2D(0, 0, size, size), mipmapLevel: 0,
                        withBytes: bytes, bytesPerRow: size * 4)

        if let queue = device.makeCommandQueue(),
           let commandBuffer = queue.makeCommandBuffer(),
           let blit = commandBuffer.makeBlitCommandEncoder() {
            blit.generateMipmaps(for: texture)
            blit.endEncoding()
            commandBuffer.commit()
        }
        return texture
    }

    public static func solid(device: MTLDevice, color: SIMD4<Float>) -> MTLTexture {
        make(device: device, size: 4) { _, _ in color }
    }

    public static func checker(device: MTLDevice, squares: Int = 8, sRGB: Bool = false,
                               a: SIMD4<Float> = [0.9, 0.9, 0.9, 1],
                               b: SIMD4<Float> = [0.35, 0.37, 0.4, 1]) -> MTLTexture {
        make(device: device, sRGB: sRGB) { u, v in
            (Int(u * Float(squares)) + Int(v * Float(squares))) % 2 == 0 ? a : b
        }
    }

    /// A wooden crate with a steel frame: a diffuse map and a matching specular map.
    public static func crate(device: MTLDevice, sRGB: Bool = false) -> (diffuse: MTLTexture, specular: MTLTexture) {
        func isSteel(_ u: Float, _ v: Float) -> Bool {
            let border: Float = 0.11
            return u < border || u > 1 - border || v < border || v > 1 - border || abs(u - v) < 0.05
        }
        func hash(_ x: Float, _ y: Float) -> Float {
            let s = sin(x * 127.1 + y * 311.7) * 43758.5453
            return s - floor(s)
        }
        let diffuse = make(device: device, sRGB: sRGB) { u, v in
            if isSteel(u, v) {
                let g = 0.42 + 0.2 * hash(floor(u * 90), floor(v * 9))
                return [g, g + 0.01, g + 0.04, 1]
            }
            let grain = 0.75 + 0.25 * hash(floor(u * 64), floor(v * 6))
            let gap: Float = abs((u * 5).truncatingRemainder(dividingBy: 1) - 0.5) > 0.46 ? 0.45 : 1
            return SIMD4<Float>(0.62 * grain * gap, 0.40 * grain * gap, 0.20 * grain * gap, 1)
        }
        let specular = make(device: device) { u, v in
            guard isSteel(u, v) else { return [0, 0, 0, 1] }
            let s = 0.4 + 0.6 * hash(floor(u * 90), floor(v * 9))
            return [s, s, s, 1]
        }
        return (diffuse, specular)
    }
}
