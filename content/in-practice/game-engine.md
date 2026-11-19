# A Game Engine

Every chapter so far built one technique in isolation: a shadow map here, a bloom chain there, each in its own small program. This chapter and the next three put them together. The result is the **LearnMetal Engine**: a small game engine made entirely with Metal, written twice, once in Swift and once in C++, with a complete little game on top and an editor to build scenes with.

It is deliberately small. The engine is between five and six thousand lines in either language, comments included, and it is meant to be read. Nothing in it is a technique you have not met in these pages; what is new is how the pieces are arranged so that they work together.

<p><a class="cta" href="{{engine-repo}}">Get the engine on GitHub</a> <a class="cta ghost" href="{{engine-repo}}/archive/refs/heads/main.zip">Download it as a .zip</a></p>

## Get it and run it

The engine lives in a repository of its own. You need macOS 13 or later and Xcode 15 or later.

<!-- swift -->
```sh
git clone {{engine-repo}}.git
cd learnmetal-engine
swift run Marble
```

Open `Package.swift` in Xcode instead if you want the debugger and the GPU tools.
<!-- /swift -->

<!-- cpp -->
The C++ version also needs CMake 3.24 or later. The first configuration downloads the four libraries it uses: GLFW, metal-cpp, stb and miniaudio.

```sh
git clone {{engine-repo}}.git
cd learnmetal-engine
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/marble
```
<!-- /cpp -->

That starts **Marble**, the sample game. Roll with W A S D, jump with Space, look around with the arrow keys or by dragging the mouse. Collect the eight gems and reach the glowing disc. A gamepad works too.

Press **F1** for statistics and **F2** to see the physics shapes.

!!! note "Where the pictures come from"
    The images in these chapters were not taken on a Mac. They were produced by a test program that runs the engine's real shaders on the CPU, which is how the engine was tested while it was being written. On a GPU you should see the same picture, with edges smoothed by multisampling.

## What an engine adds

The example programs of this site each have a renderer class that knows exactly what it draws: "a cube and a floor", "nine spheres". That stops working the moment the list of things to draw is decided while the program runs. An engine is what you get when you separate **what exists** from **how it is drawn**:

- A **scene** holds the things that exist: entities with a position, a mesh, a light, a physics body.
- A **renderer** draws whatever is in the scene, without knowing what game it is.
- **Systems** change the scene over time: physics, particles, the game's own logic.
- A **loop** runs all of them in a fixed order, every frame.

Around those sit the services a game takes for granted: loading files, input, sound, a way to draw an interface.

## The shape of a game

A game is an object with a few functions that the engine calls at the right moments. Here is a complete one: a cube that turns, lit by a sun, with a shadow.

```swift
import Foundation
import LMEngine
import simd

final class Spin: Game {
    var cube = Entity.invalid

    func start(_ engine: Engine) {
        let scene = engine.scene

        let camera = scene.create("Camera")
        scene.add(camera, Transform(position: Vec3(0, 1.5, 4), rotation: .lookRotation(forward: Vec3(0, -0.35, -1))))
        scene.add(camera, Camera())

        let sun = scene.create("Sun")
        scene.add(sun, Transform(rotation: .lookRotation(forward: Vec3(0.4, -1, -0.3))))
        scene.add(sun, Light(type: .directional, intensity: 3, castsShadows: true))

        cube = scene.create("Cube")
        scene.add(cube, Transform())
        scene.add(cube, MeshRenderer(mesh: engine.assets.cube, material: engine.assets.makeMaterial(baseColor: Vec4(0.9, 0.4, 0.1, 1))))
    }

    func update(_ engine: Engine, dt: Float) {
        engine.scene[cube, Transform.self]?.rotation = Quat(angle: Float(engine.time.elapsed), axis: Vec3(0, 1, 0))
    }
}

let engine = Engine(config: EngineConfig.fromArguments(CommandLine.arguments))
exit(engine.run(Spin()))
```

There is no render pass in it, no pipeline state, no buffer. The game says what exists; everything from the earlier chapters happens inside `engine.run`.

Notice how the camera and the sun are aimed. Both look down their own negative z axis, like the camera of the [Camera](../getting-started/camera.html) chapter, so giving them a rotation is giving them a direction.

## The frame

`Engine` owns the loop. Every frame it does the same things in the same order:

```swift
private func simulate(_ game: Game, realDelta: Double) {
    // Physics and the game's fixedUpdate advance in steps of constant length.
    let steps = time.beginFrame(realDelta)
    for _ in 0..<steps {
        game.fixedUpdate(self, dt: time.fixedDelta)
        runBehaviors(isFixedStep: true, dt: time.fixedDelta)
        physics.step(scene, dt: time.fixedDelta)
        scene.flushDestroyed()
    }
    // Show bodies where they are between the last two steps, for smooth motion at any frame rate.
    physics.writeTransforms(scene, alpha: time.alpha)

    game.update(self, dt: time.delta)
    runBehaviors(isFixedStep: false, dt: time.delta)
    scene.flushDestroyed()
    scene.updateTransforms()
    updateParticles(scene, dt: time.delta)

    canvas.begin(size: screenSize)
    game.draw(self, canvas: canvas)
    if showsColliders { drawColliders() }
    if showsStatistics { drawStatistics() }
}
```

After this the renderer draws the scene, and then the 2D canvas on top of it.

The order is not arbitrary. Physics runs before the game's `update`, so game logic sees where things ended up. World matrices are computed after everything that can move an entity, and before the two systems that need them: particles and the renderer. Entities that were destroyed during the frame are only removed at fixed points, so that no system ever holds a reference to something that vanished halfway through.

## A fixed step for physics

Rendering takes a different amount of time every frame. If physics advanced by that same varying amount, a ball would bounce a little differently on every machine, and a slow frame could push it through a floor. So physics always advances by exactly one sixtieth of a second, and the engine decides how many such steps fit in the time that has passed:

```swift
accumulator += Double(delta)
var steps = 0
while accumulator >= Double(fixedDelta) && steps < maxStepsPerFrame {
    accumulator -= Double(fixedDelta)
    steps += 1
}
if steps == maxStepsPerFrame { accumulator = min(accumulator, Double(fixedDelta)) }
alpha = Float(accumulator / Double(fixedDelta))
```

Real time is poured into the accumulator and taken out in fixed portions. On a 120 Hz display, every other frame runs no step at all; after a hiccup, one frame runs several, up to a limit.

What is left in the accumulator is a fraction of a step, `alpha`. The renderer does not show bodies at their latest physics position, but at a blend between the previous one and the latest one, `alpha` of the way along. That is what makes motion smooth even though physics only knows sixty moments per second.

One consequence is worth remembering: a function that runs "zero, one or several times per frame" is the wrong place to ask whether a key was just pressed. Read input in `update` and remember it; apply forces in `fixedUpdate`.

## One source of truth for the GPU

Every chapter with a uniform buffer had the same warning: the struct in the shader and the struct in the host code must match byte for byte, and nothing checks it. In an engine with a dozen such structs and two host languages, hoping is not enough.

The engine declares each struct once, in a C header that all three compilers read. Inside a shader the `simd` names are made to mean the shader's own types. Shortened to one struct, the header looks like this:

```cpp
// Shaders/Shared/ShaderTypes.h
#ifdef __METAL_VERSION__
typedef float2 simd_float2;
typedef float3 simd_float3;
typedef float4 simd_float4;
typedef float3x3 simd_float3x3;
typedef float4x4 simd_float4x4;
#else
#include <simd/simd.h>
#include <stdint.h>
#endif

enum {
    LMBufferVertices  = 0,   // mesh vertices, described by the vertex descriptor
    LMBufferPass      = 1,   // PassUniforms: the camera of the current pass
    LMBufferInstances = 2,   // InstanceData[], indexed by instance_id
    LMBufferMaterial  = 3,   // MaterialUniforms
    LMBufferFrame     = 4,   // FrameUniforms: sun, shadows, environment, fog
    LMBufferLights    = 5,   // LightData[]
};

typedef struct {
    simd_float4x4 model;
    simd_float4x4 normalMatrix;      // inverse transpose of model
    simd_float4 tint;                // multiplies the material's base color
} InstanceData;
```

The shaders include it with `#include`. The host code brings it in like this:

```swift
// Package.swift: a C target whose only header is ShaderTypes.h
.target(name: "ShaderTypes", path: "Shaders/Shared", publicHeadersPath: "."),
.target(name: "LMEngine", dependencies: ["ShaderTypes"], path: "Swift/LMEngine"),

// Rendering/GPUTypes.swift: Swift-style names for the C constants
import ShaderTypes

enum BufferIndex {
    static let vertices = Int(LMBufferVertices)
    static let pass = Int(LMBufferPass)
    static let instances = Int(LMBufferInstances)
    static let material = Int(LMBufferMaterial)
    static let frame = Int(LMBufferFrame)
    static let lights = Int(LMBufferLights)
}

// Rendering/RenderPasses.swift
encoder.setVertexBuffer(batch.instances.buffer, offset: batch.instances.offset, index: BufferIndex.instances)
```

The binding slots live in the same header, so `[[buffer(LMBufferInstances)]]` in a shader and the index passed to the encoder are the same constant, not two numbers that happen to agree.

Two rules keep the header safe. No `bool`, whose size differs between languages. And remember that a `float3` occupies sixteen bytes in all three languages: the unit tests check the size of every struct, so a mistake fails a test and not a frame.

## Where each chapter went

| Chapter | In the engine |
| --- | --- |
| [Shaders](../getting-started/shaders.html) | `Rendering/ShaderLibrary`, which compiles the `.metal` files at startup and reloads them when they change |
| [Textures](../getting-started/textures.html) | `Rendering/Texture`, `Assets/Assets` |
| [Transformations](../getting-started/transformations.html), [Camera](../getting-started/camera.html) | `Math/Math`, `Scene/Scene` |
| [Multiple Lights](../lighting/multiple-lights.html) | `Shaders/Lighting.metal` |
| [Model](../model-loading/model.html) | `Assets/MeshData`, with its own reader for OBJ files |
| [Blending](../advanced-metal/blending.html), [Face Culling](../advanced-metal/face-culling.html) | transparent and cut-out materials in `Rendering/RenderPasses` |
| [Render Targets](../advanced-metal/render-targets.html), [Anti-Aliasing](../advanced-metal/anti-aliasing.html) | the HDR, multisampled main pass |
| [Cubemaps](../advanced-metal/cubemaps.html) | `Rendering/Environment`, `Shaders/Sky.metal` |
| [Instancing](../advanced-metal/instancing.html) | automatic, in `Renderer.makeBatches` |
| [Shadow Mapping](../advanced-lighting/shadow-mapping.html) | `Rendering/Cascades`: four shadow maps instead of one |
| [Normal Mapping](../advanced-lighting/normal-mapping.html) | tangents in `Assets/MeshData`, `Shaders/Forward.metal` |
| [HDR](../advanced-lighting/hdr.html), [Bloom](../advanced-lighting/bloom.html), [SSAO](../advanced-lighting/ssao.html) | `Shaders/Post.metal` |
| [PBR](../pbr/lighting.html), [Diffuse Irradiance](../pbr/diffuse-irradiance.html), [Specular IBL](../pbr/specular-ibl.html) | `Shaders/Lighting.metal`, `Shaders/IBL.metal` |
| [Debugging](debugging.html) | labels on every pass, `Rendering/DebugDraw` |
| [Text Rendering](text-rendering.html), [A 2D Game](2d-game.html) | `Rendering/Canvas`, with distance-field fonts |
| [Tile-Based GPUs](../apple-platforms/tile-based-gpus.html) | memoryless targets, load and store actions chosen per pass |

Not everything made it. There are no [stencil outlines](../advanced-metal/stencil-testing.html), no [deferred path](../advanced-lighting/deferred-shading.html), no [shadows from point lights](../advanced-lighting/point-shadows.html), no [parallax mapping](../advanced-lighting/parallax-mapping.html), and nothing from the Beyond section. A small engine that does a few things well is a better place to add those than a large one that does everything halfway.

## What was tested, and what was not

!!! warning "Read this before you build"
    The engine was written without access to a Mac. The C++ version was compiled against Apple's real metal-cpp headers, its unit tests pass, and the whole engine and game were run against a software stand-in for Metal that executes the shaders on the CPU. It has **not** been linked or run on a real GPU. The Swift version is a file-by-file port of that C++ code and has **never been compiled**. The shaders have never been through Apple's compiler. The repository's README lists exactly what was checked, and its CI workflow builds everything on a Mac: expect to fix a few compile errors the first time, most likely in the Swift files that talk to AppKit and AVFoundation.

The [next chapter](engine-renderer.html) opens the renderer.
