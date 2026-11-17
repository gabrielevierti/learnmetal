# Example Code

The repository includes a Swift package with runnable examples for the main chapters. Each one is a small macOS app in a single `main.swift` plus a `Shaders.metal` file.

<p><a class="cta" href="../downloads/learnmetal-examples.zip">Download all examples (.zip)</a></p>

## Running an example

You need macOS 13 or later and Xcode 15 or later. In the unzipped folder:

```sh
swift run HelloTriangle
swift run -c release Instancing
```

You can also open `Package.swift` in Xcode, choose an example from the scheme menu and press Run. That gives you API validation, the GPU frame debugger and the performance HUD described in [Debugging](../in-practice/debugging.html).

## The examples

| Target | Chapters |
| --- | --- |
| `HelloView` | [Hello View](../getting-started/hello-view.html) |
| `HelloTriangle` | [Hello Triangle](../getting-started/hello-triangle.html) |
| `Shaders` | [Shaders](../getting-started/shaders.html) |
| `Textures` | [Textures](../getting-started/textures.html) |
| `Transformations` | [Transformations](../getting-started/transformations.html) |
| `CoordinateSystems` | [Coordinate Systems](../getting-started/coordinate-systems.html) |
| `Camera` | [Camera](../getting-started/camera.html) |
| `BasicLighting` | [Colors](../lighting/colors.html), [Basic Lighting](../lighting/basic-lighting.html), [Materials](../lighting/materials.html) |
| `LightingMaps` | [Lighting Maps](../lighting/lighting-maps.html) |
| `MultipleLights` | [Light Casters](../lighting/light-casters.html), [Multiple Lights](../lighting/multiple-lights.html) |
| `ModelLoading` | [Model I/O](../model-loading/model-io.html), [Mesh](../model-loading/mesh.html), [Model](../model-loading/model.html) |
| `RenderTargets` | [Render Targets](../advanced-metal/render-targets.html) |
| `Instancing` | [Instancing](../advanced-metal/instancing.html) |
| `ShadowMapping` | [Shadow Mapping](../advanced-lighting/shadow-mapping.html) |
| `HDRBloom` | [HDR](../advanced-lighting/hdr.html), [Bloom](../advanced-lighting/bloom.html) |
| `PBR` | [PBR Lighting](../pbr/lighting.html) |
| `ComputeParticles` | [Compute Shaders](../beyond/compute-shaders.html) |

Chapters that are not in this list have their code inline only.

## How they differ from the chapters

- **No Xcode project.** The chapters build a SwiftUI app. The examples use a small library, `LearnMetalKit`, that opens a plain AppKit window, so each example is one file.
- **Shaders are compiled at launch** from the `Shaders.metal` text with `makeLibrary(source:)`. That lets `swift run` work without Xcode's Metal build step. Shader errors are printed to the console.
- **Textures are generated in code**, so there is nothing else to download.
- **Examples 01 to 03 write the frame loop by hand.** Later ones inherit it from a `BaseRenderer` class to stay short.

## About the figures

The images in the chapters are illustrations. They are drawn by a small software renderer in the repository's `tools/` folder, which implements the same math as each chapter's shaders with numpy. They are not screenshots of the Metal examples, so expect small differences in textures and framing when you run the code.
