import MetalKit
import QuartzCore

/// Per-draw vertex uniforms shared by most examples. Mirrors `Uniforms` in the shaders.
public struct SceneUniforms {
    public var model: float4x4
    public var view: float4x4
    public var projection: float4x4
    public var normalMatrix: float3x3

    public init(model: float4x4, view: float4x4, projection: float4x4) {
        self.model = model
        self.view = view
        self.projection = projection
        self.normalMatrix = model.normalMatrix
    }
}

/// Loads `Shaders.metal` from an example's resource bundle and compiles it.
///
/// The chapters let Xcode compile .metal files at build time. Compiling at launch instead
/// lets the examples run with a plain `swift run`, and shader errors are printed to the console.
public func makeShaderLibrary(device: MTLDevice, bundle: Bundle, name: String = "Shaders") -> MTLLibrary {
    if let url = bundle.url(forResource: name, withExtension: "metal"),
       let source = try? String(contentsOf: url, encoding: .utf8) {
        do {
            return try device.makeLibrary(source: source, options: nil)
        } catch {
            fatalError("Could not compile \(name).metal:\n\(error)")
        }
    }
    if let library = try? device.makeDefaultLibrary(bundle: bundle) {
        return library                      // Xcode precompiled the file instead of copying it
    }
    fatalError("Could not find \(name).metal in the resource bundle")
}

public enum Blending {
    case none, alpha, additive
}

public func makePipeline(device: MTLDevice, library: MTLLibrary,
                         vertex: String, fragment: String?,
                         colorFormats: [MTLPixelFormat],
                         depthFormat: MTLPixelFormat = .invalid,
                         vertexDescriptor: MTLVertexDescriptor? = nil,
                         blending: Blending = .none,
                         label: String? = nil) -> MTLRenderPipelineState {
    let descriptor = MTLRenderPipelineDescriptor()
    descriptor.label = label ?? vertex
    descriptor.vertexFunction = library.makeFunction(name: vertex)
    descriptor.fragmentFunction = fragment.flatMap { library.makeFunction(name: $0) }
    descriptor.vertexDescriptor = vertexDescriptor
    descriptor.depthAttachmentPixelFormat = depthFormat
    for (index, format) in colorFormats.enumerated() {
        let attachment = descriptor.colorAttachments[index]!
        attachment.pixelFormat = format
        switch blending {
        case .none:
            break
        case .alpha:
            attachment.isBlendingEnabled = true
            attachment.sourceRGBBlendFactor = .sourceAlpha
            attachment.destinationRGBBlendFactor = .oneMinusSourceAlpha
            attachment.sourceAlphaBlendFactor = .one
            attachment.destinationAlphaBlendFactor = .oneMinusSourceAlpha
        case .additive:
            attachment.isBlendingEnabled = true
            attachment.sourceRGBBlendFactor = .one
            attachment.destinationRGBBlendFactor = .one
            attachment.sourceAlphaBlendFactor = .one
            attachment.destinationAlphaBlendFactor = .one
        }
    }
    do {
        return try device.makeRenderPipelineState(descriptor: descriptor)
    } catch {
        fatalError("Could not create pipeline \(descriptor.label ?? ""): \(error)")
    }
}

public func makeDepthState(device: MTLDevice, compare: MTLCompareFunction = .less,
                           write: Bool = true) -> MTLDepthStencilState {
    let descriptor = MTLDepthStencilDescriptor()
    descriptor.depthCompareFunction = compare
    descriptor.isDepthWriteEnabled = write
    return device.makeDepthStencilState(descriptor: descriptor)!
}

public func makeSampler(device: MTLDevice, address: MTLSamplerAddressMode = .repeat,
                        filter: MTLSamplerMinMagFilter = .linear,
                        compare: MTLCompareFunction? = nil) -> MTLSamplerState {
    let descriptor = MTLSamplerDescriptor()
    descriptor.minFilter = filter
    descriptor.magFilter = filter
    descriptor.mipFilter = filter == .linear ? .linear : .notMipmapped
    descriptor.sAddressMode = address
    descriptor.tAddressMode = address
    if let compare {
        descriptor.compareFunction = compare
        descriptor.mipFilter = .notMipmapped
    }
    return device.makeSamplerState(descriptor: descriptor)!
}

/// A texture that a render pass can draw into and a later pass can sample.
public func makeRenderTarget(device: MTLDevice, format: MTLPixelFormat, width: Int, height: Int,
                             label: String) -> MTLTexture {
    let descriptor = MTLTextureDescriptor.texture2DDescriptor(
        pixelFormat: format, width: max(width, 1), height: max(height, 1), mipmapped: false)
    descriptor.usage = [.renderTarget, .shaderRead]
    descriptor.storageMode = .private
    let texture = device.makeTexture(descriptor: descriptor)!
    texture.label = label
    return texture
}

public extension MTLRenderCommandEncoder {
    /// Copies a small value into the vertex buffer table, like `setVertexBytes`.
    func setVertexValue<T>(_ value: T, index: Int) {
        var copy = value
        setVertexBytes(&copy, length: MemoryLayout<T>.stride, index: index)
    }

    func setFragmentValue<T>(_ value: T, index: Int) {
        var copy = value
        setFragmentBytes(&copy, length: MemoryLayout<T>.stride, index: index)
    }
}

/// Shared frame loop for the later examples: timing, the fly camera, the command buffer
/// and presentation. Subclasses override `render(in:commandBuffer:)`.
///
/// Examples 01 to 03 write this loop out by hand, exactly as the first chapters do.
open class BaseRenderer: NSObject, MTKViewDelegate {
    public let device: MTLDevice
    public let commandQueue: MTLCommandQueue
    public let camera = Camera()
    public private(set) var aspect: Float = 1
    public private(set) var time: Float = 0
    public private(set) var deltaTime: Float = 0

    private let startTime = CACurrentMediaTime()
    private var lastTime = CACurrentMediaTime()

    /// - Parameter depth: when true, the view gets a `.depth32Float` depth texture.
    public init(view: MTKView, depth: Bool = true) {
        device = view.device!
        commandQueue = device.makeCommandQueue()!
        super.init()
        view.depthStencilPixelFormat = depth ? .depth32Float : .invalid
        view.clearDepth = 1
        if view.drawableSize.height > 0 {
            aspect = Float(view.drawableSize.width / view.drawableSize.height)
        }
    }

    /// View and projection for the current camera, combined with a model matrix.
    public func sceneUniforms(model: float4x4) -> SceneUniforms {
        SceneUniforms(model: model, view: camera.viewMatrix, projection: camera.projectionMatrix(aspect: aspect))
    }

    open func resize(to size: CGSize) {}

    open func render(in view: MTKView, commandBuffer: MTLCommandBuffer) {}

    public func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {
        if size.height > 0 { aspect = Float(size.width / size.height) }
        resize(to: size)
    }

    public func draw(in view: MTKView) {
        let now = CACurrentMediaTime()
        deltaTime = Float(min(now - lastTime, 0.1))
        lastTime = now
        time = Float(now - startTime)
        camera.update(deltaTime: deltaTime)

        guard let commandBuffer = commandQueue.makeCommandBuffer() else { return }
        render(in: view, commandBuffer: commandBuffer)
        if let drawable = view.currentDrawable {
            commandBuffer.present(drawable)
        }
        commandBuffer.commit()
    }
}
