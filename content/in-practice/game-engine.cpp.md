```cpp
#include "LMEngine.hpp"
using namespace lm;

struct Spin : Game {
    Entity cube;

    void start(Engine& engine) override {
        Scene& scene = engine.scene;

        Entity camera = scene.create("Camera");
        Transform view;
        view.position = Vec3{0, 1.5f, 4};
        view.rotation = lookRotation(Vec3{0, -0.35f, -1});
        scene.add(camera, view);
        scene.add(camera, Camera{});

        Entity sun = scene.create("Sun");
        Transform sunDirection;
        sunDirection.rotation = lookRotation(Vec3{0.4f, -1, -0.3f});
        scene.add(sun, sunDirection);
        Light light;
        light.type = LightType::Directional;
        light.intensity = 3;
        light.castsShadows = true;
        scene.add(sun, light);

        cube = scene.create("Cube");
        scene.add(cube, Transform{});
        scene.add(cube, MeshRenderer{engine.assets().cube(), engine.assets().makeMaterial(Vec4{0.9f, 0.4f, 0.1f, 1})});
    }

    void update(Engine& engine, float) override {
        engine.scene.get<Transform>(cube)->rotation = axisAngle(Vec3{0, 1, 0}, float(engine.time.elapsed));
    }
};

int main(int argc, char** argv) {
    Engine engine(EngineConfig::fromArguments(argc, argv));
    Spin game;
    return engine.run(game);
}
```

```cpp
void Engine::simulate(Game& game, double realDelta) {
    // Physics and the game's fixedUpdate advance in steps of constant length.
    int steps = time.beginFrame(realDelta);
    for (int i = 0; i < steps; i++) {
        game.fixedUpdate(*this, time.fixedDelta);
        runBehaviors(true, time.fixedDelta);
        physics.step(scene, time.fixedDelta);
        scene.flushDestroyed();
    }
    // Show bodies where they are between the last two steps, for smooth motion at any frame rate.
    physics.writeTransforms(scene, time.alpha);

    game.update(*this, time.delta);
    runBehaviors(false, time.delta);
    scene.flushDestroyed();
    scene.updateTransforms();
    updateParticles(scene, time.delta);

    canvas_.begin(screenSize());
    game.draw(*this, canvas_);
    if (showsColliders) drawColliders();
    if (showsStatistics) drawStatistics();
}
```

```cpp
accumulator_ += delta;
int steps = 0;
while (accumulator_ >= fixedDelta && steps < maxStepsPerFrame) {
    accumulator_ -= fixedDelta;
    steps++;
}
if (steps == maxStepsPerFrame) accumulator_ = std::min(accumulator_, double(fixedDelta));
alpha = float(accumulator_ / fixedDelta);
```

```cpp
// Rendering/GPUTypes.hpp: the same header, inside a namespace
#include <simd/simd.h>

#include <cstdint>

namespace lm::gpu {
#include "ShaderTypes.h"
}

// Rendering/RenderPasses.cpp
encoder->setVertexBuffer(batch.instances.buffer, batch.instances.offset, gpu::LMBufferInstances);
```
