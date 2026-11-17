import AppKit
import MetalKit

/// Keys used by the examples (macOS virtual key codes).
public enum Key: UInt16 {
    case a = 0, s = 1, d = 2, w = 13, q = 12, e = 14
    case one = 18, two = 19, three = 20, four = 21
    case space = 49
}

/// Polled keyboard and mouse state, so a render loop can ask "is W down right now?".
public final class Input {
    public static let shared = Input()

    private var keys = Set<UInt16>()
    private var pressed = Set<UInt16>()
    private var mouseDelta = SIMD2<Float>(0, 0)
    private var scrollDelta: Float = 0

    public func isDown(_ key: Key) -> Bool { keys.contains(key.rawValue) }

    /// True once for each press of the key.
    public func wasPressed(_ key: Key) -> Bool { pressed.remove(key.rawValue) != nil }

    /// Mouse movement while the left button is held, since the last call.
    public func takeMouseDelta() -> SIMD2<Float> {
        defer { mouseDelta = .zero }
        return mouseDelta
    }

    public func takeScroll() -> Float {
        defer { scrollDelta = 0 }
        return scrollDelta
    }

    func install() {
        NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .keyUp, .leftMouseDragged, .scrollWheel]) { event in
            switch event.type {
            case .keyDown:
                if event.modifierFlags.contains(.command) { return event }
                if !event.isARepeat { self.pressed.insert(event.keyCode) }
                self.keys.insert(event.keyCode)
                return nil                      // swallow the event so the system does not beep
            case .keyUp:
                self.keys.remove(event.keyCode)
                return nil
            case .leftMouseDragged:
                self.mouseDelta += SIMD2(Float(event.deltaX), Float(event.deltaY))
            case .scrollWheel:
                self.scrollDelta += Float(event.scrollingDeltaY)
            default:
                break
            }
            return event
        }
    }
}

private final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

/// Opens a window containing an MTKView and runs the app. Never returns.
///
/// `makeRenderer` receives the view, already connected to the default Metal device,
/// and returns the object that will draw into it.
@MainActor
public func runApp(title: String, width: Int = 960, height: Int = 600,
                   makeRenderer: (MTKView) -> MTKViewDelegate) -> Never {
    guard let device = MTLCreateSystemDefaultDevice() else {
        fatalError("Metal is not supported on this machine")
    }
    let app = NSApplication.shared
    app.setActivationPolicy(.regular)

    let frame = NSRect(x: 0, y: 0, width: width, height: height)
    let window = NSWindow(contentRect: frame,
                          styleMask: [.titled, .closable, .miniaturizable, .resizable],
                          backing: .buffered, defer: false)
    window.title = title

    let view = MTKView(frame: frame, device: device)
    view.colorPixelFormat = .bgra8Unorm
    view.clearColor = MTLClearColor(red: 0.2, green: 0.3, blue: 0.3, alpha: 1)

    let renderer = makeRenderer(view)       // MTKView holds its delegate weakly; this keeps it alive
    view.delegate = renderer
    window.contentView = view
    window.center()
    window.makeKeyAndOrderFront(nil)

    let mainMenu = NSMenu()
    let appItem = NSMenuItem()
    let appMenu = NSMenu()
    appMenu.addItem(NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
    appItem.submenu = appMenu
    mainMenu.addItem(appItem)
    app.mainMenu = mainMenu

    let delegate = AppDelegate()
    app.delegate = delegate
    Input.shared.install()
    app.activate(ignoringOtherApps: true)

    withExtendedLifetime((renderer, delegate, window)) {
        app.run()
    }
    exit(0)
}
