// Chapter: Getting Started / Hello View
// Clears the window to a color every frame. The whole frame loop is written out by hand.

import LearnMetalKit
import MetalKit

final class Renderer: NSObject, MTKViewDelegate {
    let device: MTLDevice
    let commandQueue: MTLCommandQueue

    init(view: MTKView) {
        device = view.device!
        commandQueue = device.makeCommandQueue()!
        super.init()
        view.colorPixelFormat = .bgra8Unorm
        view.clearColor = MTLClearColor(red: 0.2, green: 0.3, blue: 0.3, alpha: 1.0)
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {
        print("Drawable size: \(Int(size.width)) x \(Int(size.height)) pixels")
    }

    func draw(in view: MTKView) {
        guard let passDescriptor = view.currentRenderPassDescriptor,
              let drawable = view.currentDrawable,
              let commandBuffer = commandQueue.makeCommandBuffer(),
              let encoder = commandBuffer.makeRenderCommandEncoder(descriptor: passDescriptor) else {
            return
        }

        // Draw calls would go here.

        encoder.endEncoding()
        commandBuffer.present(drawable)
        commandBuffer.commit()
    }
}

runApp(title: "01 Hello View") { view in Renderer(view: view) }
