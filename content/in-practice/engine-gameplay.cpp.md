```cpp
/// Something to collect. The entity also carries a mesh, a light and a trigger collider.
struct Gem {
    lm::Vec3 home{0, 0, 0};         // the gem bobs up and down around this point
    float phase = 0;                // so that the gems do not all move in step
    lm::Vec3 color{1, 1, 1};
};

/// A platform that glides back and forth between two points.
struct MovingPlatform {
    lm::Vec3 from{0, 0, 0};
    lm::Vec3 to{0, 0, 0};
    float period = 6;               // seconds for a round trip
};

/// Destroys its entity when the time runs out: for one-shot effects.
struct Lifetime {
    float seconds = 1;
};
```

```cpp
for (const Vec3& position : gemPositions) {
    int index = level.gemCount++;
    Entity gem = scene.create("Gem");
    Transform transform;
    transform.position = position;
    transform.scale = Vec3{0.9f, 0.9f, 0.9f};
    scene.add(gem, transform);
    scene.add(gem, MeshRenderer{gemMesh, gemMaterials[index % 4]});
    scene.add(gem, Gem{position, 0.9f * float(index), gemColors[index % 4]});
    Light light;
    light.color = gemColors[index % 4];
    light.intensity = 5.0f;
    light.range = 5.0f;
    scene.add(gem, light);
    Collider trigger = Collider::sphere(0.75f);
    trigger.isTrigger = true;
    scene.add(gem, trigger);
}
```

```cpp
// Gems turn and bob; their lights and triggers move with them.
float time = float(engine.time.elapsed);
scene.each<Gem, Transform>([&](Entity, Gem& gem, Transform& transform) {
    transform.position = gem.home + Vec3{0, 0.18f * std::sin(time * 2.0f + gem.phase), 0};
    transform.rotation = axisAngle(Vec3{0, 1, 0}, time * 1.4f + gem.phase);
});
```

```cpp
scene.add(level.marble, Collider::sphere(Level::kMarbleRadius));
RigidBody marbleBody;
marbleBody.restitution = 0.35f;
marbleBody.friction = 0.03f;                // a rolling ball barely slows down by itself
marbleBody.linearDamping = 0.15f;
scene.add(level.marble, marbleBody);
```

```cpp
// The physics moves the marble but does not spin it. Turn it by the angle a ball of
// this size rolls through when it travels this far: distance divided by radius.
Vec3 flat{body->velocity.x, 0, body->velocity.z};
float speed = simd::length(flat);
if (speed > 0.05f) {
    Vec3 axis = simd::normalize(simd::cross(Vec3{0, 1, 0}, flat));
    marble->rotation = simd::normalize(axisAngle(axis, speed * dt / Level::kMarbleRadius) * marble->rotation);
}
```

```cpp
// Physics events. They arrive at the end of a physics step.
engine.physics.onTriggerEnter = [this, &engine](Entity trigger, Entity other) {
    if (other != level_.marble) return;
    if (engine.scene.has<Gem>(trigger)) {
        collect(engine, trigger);
    } else if (trigger == level_.goal && collected_ == level_.gemCount && !hasWon_) {
        hasWon_ = true;
        engine.audio().play(sounds_.win);
        spawnBurst(engine, engine.scene.get<Transform>(level_.goal)->position + Vec3{0, 0.5f, 0}, Vec3{0.4f, 1.0f, 0.5f});
    }
};
engine.physics.onContactBegin = [this, &engine](const Contact& contact) {
    if (contact.a != level_.marble && contact.b != level_.marble) return;
    if (contact.impactSpeed < 2.5f) return;
    PlayOptions options;
    options.volume = saturate(contact.impactSpeed / 12.0f);     // harder hits are louder
    options.pitch = 0.9f + 0.2f * options.volume;
    engine.audio().play(sounds_.land, options);
};
```

```cpp
// Actions: the game asks "is jump pressed?" and never mentions a key or a button again.
Input& input = engine.input;
input.bindAxis("moveX", Key::A, Key::D, GamepadAxis::LeftX);
input.bindAxis("moveY", Key::S, Key::W, GamepadAxis::LeftY);
input.bindAxis("lookX", Key::Left, Key::Right, GamepadAxis::RightX);
input.bindAxis("lookY", Key::Down, Key::Up, GamepadAxis::RightY);
input.bindButton("jump", {Key::Space}, {GamepadButton::A});
input.bindButton("restart", {Key::R}, {GamepadButton::Start});
input.bindButton("quit", {Key::Escape}, {GamepadButton::Back});
```

```cpp
// Input is read here, once per frame, and remembered for the fixed steps.
if (!isDemo) {
    wish_ = Vec2{input.axis("moveX"), input.axis("moveY")};
    float length = simd::length(wish_);
    if (length > 1.0f) wish_ /= length;             // diagonals are not faster
    if (input.wasPressed("jump")) jumpBuffer_ = 0.15f;
    if (length > 0.1f) hasMoved_ = true;
}
```

```cpp
// Push the marble where the stick points, relative to where the camera looks.
// (The autopilot thinks in compass directions instead: east and north.)
if (!hasWon_) {
    Vec3 forward{-std::sin(cameraYaw_), 0, -std::cos(cameraYaw_)};
    Vec3 right{std::cos(cameraYaw_), 0, -std::sin(cameraYaw_)};
    if (isDemo) {
        Autopilot::Command command = autopilot_.steer(engine, level_);
        wish_ = command.push;
        if (command.jump) jumpBuffer_ = 0.15f;
        forward = Vec3{0, 0, -1};
        right = Vec3{1, 0, 0};
        if (simd::length(wish_) > 0.1f) hasMoved_ = true;
    }
    Vec3 push = right * wish_.x + forward * wish_.y;
    float control = body->isGrounded ? 1.0f : kAirControl;
    body->velocity += push * (kAcceleration * control * dt);

    // A speed limit on the ground plane only, so that falling stays fast.
    Vec3 flat{body->velocity.x, 0, body->velocity.z};
    float speed = simd::length(flat);
    if (speed > kMaxSpeed) {
        flat *= kMaxSpeed / speed;
        body->velocity = Vec3{flat.x, body->velocity.y, flat.z};
    }

    jumpBuffer_ -= dt;
    if (jumpBuffer_ > 0 && body->isGrounded) {
        body->velocity.y = kJumpSpeed;
        jumpBuffer_ = 0;
        engine.audio().play(sounds_.jump);
    }
}
```

```cpp
// The moving platform carries the marble across the gap between terrace and landing.
Entity platform = builder.block("Ferry", Vec3{17, 2.25f, -12.4f}, Vec3{3, 0.5f, 3}, paint);
RigidBody ferryBody;
ferryBody.type = BodyType::Kinematic;       // it moves, but nothing can push it
ferryBody.friction = 1.0f;
scene.add(platform, ferryBody);
scene.add(platform, MovingPlatform{Vec3{17, 2.25f, -12.4f}, Vec3{17, 2.25f, -6.6f}, 9.0f});
level.ferry = platform;
```

```cpp
// Moving platforms: a kinematic body goes where its velocity takes it, so the
// platform is steered by setting the velocity that leads to where it should be next.
float time = float(engine.time.elapsed);
scene.each<MovingPlatform, RigidBody>([&](Entity, MovingPlatform& platform, RigidBody& platformBody) {
    float t = 0.5f - 0.5f * std::cos((time + dt) / platform.period * 2.0f * kPi);      // 0 -> 1 -> 0, easing at the ends
    Vec3 target = lerp(platform.from, platform.to, t);
    platformBody.velocity = (target - platformBody.position) / dt;
});
```

```cpp
SynthParams note(Waveform waveform, float frequency, float duration, float volume) {
    SynthParams params;
    params.waveform = waveform;
    params.frequency = frequency;
    params.duration = duration;
    params.volume = volume;
    params.release = duration * 0.6f;
    return params;
}

// Then, in Sounds::make():

// Two quick notes a fifth apart: the classic "got it" chime.
sounds.collect = share(synthesizeSequence({note(Waveform::Triangle, 880.0f, 0.07f, 0.35f),
                                           note(Waveform::Triangle, 1318.5f, 0.22f, 0.35f)}));

// A pitch that slides up reads as "going up"; down, as falling.
SynthParams jump = note(Waveform::Sine, 260.0f, 0.16f, 0.4f);
jump.frequencyEnd = 520.0f;
sounds.jump = share(synthesize(jump));
```

```cpp
// The rumble gets louder and higher with speed, and stops in the air.
float rolling = body->isGrounded ? saturate(speed / kMaxSpeed) : 0.0f;
engine.audio().mixer().setVolume(rollSound_, 0.16f * rolling);
engine.audio().mixer().setPitch(rollSound_, 0.08f + 0.1f * rolling);
```

```cpp
// Gems, top left.
canvas.rect(Vec2{16, 16}, Vec2{132, 44}, panel);
canvas.circle(Vec2{40, 38}, 9, rgb(0x3fd0ff), 6);       // six segments: a hexagon, close enough to a gem
std::snprintf(text, sizeof(text), "%d / %d", collected_, level_.gemCount);
float pulse = 22.0f + 8.0f * collectPulse_;
canvas.text(text, Vec2{60, 38 - pulse * 0.6f}, pulse, white);

// The clock, top right.
int minutes = int(playTime_) / 60;
float seconds = playTime_ - float(minutes * 60);
std::snprintf(text, sizeof(text), "%d:%05.2f", minutes, double(seconds));
canvas.rect(Vec2{size.x - 136, 16}, Vec2{120, 44}, panel);
canvas.text(text, Vec2{size.x - 28, 25}, 22, white, TextAlign::Right);
```

```cpp
// Steering: decide the velocity we would like (toward the target, slower when close),
// then push in proportion to how far the real velocity is from it. On the ferry the
// velocity we want is the ferry's own, plus whatever keeps us near its center.
Vec3 toTarget = target - marble->position;
Vec3 wanted = Vec3{toTarget.x, 0, toTarget.z} * 2.5f;
float wantedSpeed = simd::length(wanted);
if (wantedSpeed > waypoint.speed) wanted *= waypoint.speed / wantedSpeed;
if (waypoint.action == Action::Board || waypoint.action == Action::Ride) wanted += ferry->velocity;
Vec3 correction = (wanted - marble->velocity) * 0.6f;
command.push = Vec2{correction.x, -correction.z};  // north is -z
float length = simd::length(command.push);
if (length > 1.0f) command.push /= length;
return command;
```

```cpp
int main(int argc, char** argv) {
    lm::EngineConfig defaults;
    defaults.title = "Marble";
    lm::Engine engine(lm::EngineConfig::fromArguments(argc, argv, defaults));
    MarbleGame game;
    int result = engine.run(game);
    if (result == 0 && game.isDemo && engine.window() == nullptr && !game.hasWon()) {
        lm::logError("the autopilot did not finish the course");
        return 1;
    }
    return result;
}
```

```cpp
TEST(a_ball_falls_bounces_and_comes_to_rest_on_the_floor) {
    Scene scene;
    Physics physics;
    addStaticBox(scene, Vec3{0, -0.5f, 0}, Vec3{10, 0.5f, 10});
    Entity ball = addBall(scene, Vec3{0, 3, 0});
    scene.get<RigidBody>(ball)->restitution = 0.5f;

    run(physics, scene, 0.5f);
    CHECK(scene.get<RigidBody>(ball)->position.y < 3);                   // it fell
    run(physics, scene, 6.0f);
    const RigidBody& body = *scene.get<RigidBody>(ball);
    CHECK_NEAR(body.position.y, 0.5, 0.02);                              // resting on the floor, not sinking into it
    CHECK(simd::length(body.velocity) < 0.2f);
    CHECK(body.isGrounded);
    CHECK_NEAR(body.groundNormal.y, 1, 1e-3);
}
```
