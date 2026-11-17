# Project Setup

Setting up a Metal project takes minutes. There are no libraries to download, build or link: Metal and its helper framework MetalKit ship with the system.

## What you need

- A Mac running a recent version of macOS.
- Xcode, free from the Mac App Store.

The examples target macOS because it is the quickest loop: press Run and a window appears. Everything except the few lines that host the view works unchanged on iOS, and the differences are shown below.

!!! note "Simulator or device?"
    Metal works in the iOS Simulator, but with reduced features and performance. When you target iPhone or iPad, test on a real device.

## Create the project

1. In Xcode choose **File → New → Project**.
2. Pick **macOS → App**.
3. Name it `LearnMetal`, set **Interface** to **SwiftUI** and **Language** to **Swift**.

Xcode also offers a **Game** template with Metal as the technology. It generates a working spinning cube, which is nice to look at but hides the parts we want to write ourselves, so we start from a plain app.

## MetalKit and MTKView

To draw with Metal you need a surface that the system can put on screen. The low-level way is a `CAMetalLayer` plus your own display link. **MetalKit** wraps both in a view called `MTKView` that:

- owns the layer and hands you a fresh **drawable** (a texture that will be shown on screen) each frame,
- creates depth and multisample textures for you on request,
- calls your code once per display refresh.

You tell the view what to draw by giving it a **delegate**, an object that implements two methods of `MTKViewDelegate`. That delegate is our renderer, and it is where nearly all code in this series will live.

## Host the view in SwiftUI

`MTKView` is an AppKit view (UIKit on iOS), so SwiftUI needs a small adapter. Add a new Swift file `MetalView.swift`:

```swift
import SwiftUI
import MetalKit

struct MetalView: NSViewRepresentable {
    final class Coordinator {
        var renderer: Renderer?
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeNSView(context: Context) -> MTKView {
        let view = MTKView()
        context.coordinator.renderer = Renderer(view: view)
        return view
    }

    func updateNSView(_ view: MTKView, context: Context) {}
}
```

The coordinator exists for one reason: `MTKView` holds its delegate weakly, so something else must keep the renderer alive.

On iOS the adapter is the same with different names: conform to `UIViewRepresentable` and implement `makeUIView` and `updateUIView`.

Then show the view in `ContentView.swift`:

```swift
import SwiftUI

struct ContentView: View {
    var body: some View {
        MetalView()
            .frame(minWidth: 800, minHeight: 600)
    }
}
```

The project will not compile yet because `Renderer` does not exist. That is the next chapter.

## Where shaders go

Shaders live in files with the `.metal` extension. Create one with **File → New → File → Metal File** and call it `Shaders.metal`. Xcode gives it this content:

```cpp
#include <metal_stdlib>
using namespace metal;
```

Leave it for now. Any `.metal` file that belongs to the app target is compiled during the build and bundled into the app automatically.

## Turn on the safety nets

Open **Product → Scheme → Edit Scheme → Run → Diagnostics** (in some Xcode versions the Metal options are under **Options**) and make sure **Metal API Validation** is enabled. Validation checks every Metal call and stops with a readable message when you do something illegal, instead of showing a black screen. It is on by default for debug runs, and you should leave it on. **Shader Validation** in the same place catches out-of-bounds reads and similar mistakes inside shaders; turn it on whenever a shader misbehaves.

The [Debugging](../in-practice/debugging.html) chapter covers these tools in depth. You can read it at any time.
