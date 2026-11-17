# learnmetal examples

Runnable Swift programs for the learnmetal chapters. Each example is a small macOS app that opens a window and renders with Metal.

## Requirements

- macOS 13 or later
- Xcode 15 or later (or the matching command line tools)

## Run

From this folder:

```sh
swift run HelloTriangle
swift run -c release Instancing      # release builds are much faster for the heavy examples
```

Or open the package in Xcode (`open Package.swift`), pick an example in the scheme menu, and press Run. Running from Xcode gives you API validation, the GPU frame debugger and the performance HUD.

## Examples

| Target | Folder | Chapters |
| --- | --- | --- |
| `HelloView` | `01-HelloView` | Hello View |
| `HelloTriangle` | `02-HelloTriangle` | Hello Triangle |
| `Shaders` | `03-Shaders` | Shaders |
| `Textures` | `04-Textures` | Textures |
| `Transformations` | `05-Transformations` | Transformations |
| `CoordinateSystems` | `06-CoordinateSystems` | Coordinate Systems |
| `Camera` | `07-Camera` | Camera |
| `BasicLighting` | `08-BasicLighting` | Colors, Basic Lighting, Materials |
| `LightingMaps` | `09-LightingMaps` | Lighting Maps |
| `MultipleLights` | `10-MultipleLights` | Light Casters, Multiple Lights |
| `ModelLoading` | `11-ModelLoading` | Model I/O, Mesh, Model |
| `RenderTargets` | `12-RenderTargets` | Render Targets |
| `Instancing` | `13-Instancing` | Instancing |
| `ShadowMapping` | `14-ShadowMapping` | Gamma Correction, Shadow Mapping |
| `HDRBloom` | `15-HDRBloom` | HDR, Bloom |
| `PBR` | `16-PBR` | PBR Theory, PBR Lighting |
| `ComputeParticles` | `17-ComputeParticles` | Compute Shaders, Life Without Geometry Shaders |

## Controls

From example 07 on: **W A S D** move, **Q / E** go down and up, **drag** with the mouse to look around, **scroll** to zoom. Extra keys are shown in each window's title.

## How the examples differ from the chapters

- **No Xcode project.** The chapters build an app with SwiftUI. Here a small library, `LearnMetalKit`, opens a plain AppKit window so that every example is a single `main.swift`.
- **Shaders are compiled at launch.** Each example has a `Shaders.metal` file that is loaded as text and compiled with `makeLibrary(source:)`, so `swift run` works without Xcode's Metal build step. Shader errors are printed to the console.
- **Textures are generated in code**, so there are no image files to download. Replace them with `MTKTextureLoader` as the Textures chapter shows.
- **Examples 01 to 03 write the frame loop by hand**, as the first chapters do. Later examples inherit it from `BaseRenderer` to stay short. Read `Sources/LearnMetalKit/Renderer.swift` once to see what it does.

## Layout

```
Package.swift
Sources/
  LearnMetalKit/      window, input, camera, math, geometry, textures, helpers
  01-HelloView/       main.swift
  02-HelloTriangle/   main.swift, Shaders.metal
  ...
```
