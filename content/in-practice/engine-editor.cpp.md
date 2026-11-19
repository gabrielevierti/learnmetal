```cpp
if (Light* light = scene.get<Light>(selected_)) {
    gui_.heading("Light");
    int type = int(light->type);
    if (gui_.combo("Type", type, {"Directional", "Point", "Spot"})) light->type = LightType(type);
    gui_.color("Color", light->color);
    gui_.dragFloat("Intensity", light->intensity, 0.05f, 0.0f, 1000.0f);
    if (light->type != LightType::Directional) gui_.dragFloat("Range", light->range, 0.05f, 0.1f, 500.0f);
    if (light->type == LightType::Spot) {
        dragDegrees(gui_, "Inner cone", light->innerConeAngle, 0.0f, 89.0f);
        dragDegrees(gui_, "Outer cone", light->outerConeAngle, 0.0f, 89.0f);
    }
    if (light->type == LightType::Directional) gui_.checkbox("Casts shadows", light->castsShadows);
    if (gui_.button("Remove light")) scene.remove<Light>(selected_);
}
```

```cpp
bool Gui::checkbox(const std::string& label, bool& value) {
    uint64_t id = makeId(label);
    Rect row, field;
    if (!nextRow(row)) return false;
    splitRow(row, label, field);
    float side = row.size.y - 6;
    Rect box{field.position + Vec2{0, 3}, Vec2{side, side}};
    bool clicked = pressed(id, box);
    if (clicked) {
        value = !value;
        changed_ = true;
    }
    canvas_->rect(box.position, box.size, mouseFree_ && box.contains(mouse_) ? style.fieldHot : style.field);
    if (value) canvas_->rect(box.position + Vec2{4, 4}, box.size - Vec2{8, 8}, style.accent);
    return clicked;
}
```

```cpp
std::vector<NamedMaterial> materials;
loadSceneFile(engine.assets().path("Scenes/demo.scene"), engine.scene, materials, engine.renderer().settings,
              sceneAssets(engine.assets()));
```

```cpp
void Editor::createCamera(Engine& engine) {
    camera_ = engine.scene.create("Editor camera");
    Transform transform;
    transform.position = cameraPosition_;
    transform.rotation = eulerAngles(cameraPitch_, cameraYaw_);
    engine.scene.add(camera_, transform);
    engine.scene.add(camera_, Camera{});
    engine.scene.add(camera_, EditorOnly{});
    engine.renderer().cameraOverride = isPlaying_ ? Entity{} : camera_;
}
```

```cpp
/// The entity under a point of the screen: the nearest one hit by the ray through it.
Entity Editor::pick(Engine& engine, Vec2 point) const {
    Ray ray = engine.screenRay(point);
    Entity best;
    float bestDistance = std::numeric_limits<float>::max();
    for (Entity entity : entities_) {
        const Transform* transform = engine.scene.get<Transform>(entity);
        const MeshRenderer* renderer = engine.scene.get<MeshRenderer>(entity);
        std::optional<float> hit;
        if (renderer && renderer->mesh) {
            // Test against the mesh's box in the mesh's own space: bring the ray there.
            // The direction is left unnormalized, so the distance keeps its world scale.
            Mat4 toLocal = simd::inverse(transform->world);
            Ray local{transformPoint(toLocal, ray.origin), transformDirection(toLocal, ray.direction)};
            hit = intersectAABB(local, renderer->mesh->bounds());
        } else {
            hit = intersectSphere(ray, transform->worldPosition(), 0.35f);     // lights and cameras: their icon
        }
        if (hit && *hit < bestDistance) {
            bestDistance = *hit;
            best = entity;
        }
    }
    return best;
}
```

```cpp
if (dragAxis_ == i) {
    // How far the pointer moved along the handle, in points.
    float travel = simd::dot(input.mouseDelta(), dragDirection_);
    if (tool == Tool::Move) {
        Vec3 delta = axis * (travel / dragPointsPerUnit_);
        // Transform::position is relative to the parent: express the step there.
        if (const Transform* parent = engine.scene.get<Transform>(transform->parent)) {
            delta = transformDirection(simd::inverse(parent->world), delta);
        }
        transform->position += delta;
    } else if (tool == Tool::Rotate) {
        transform->rotation = simd::normalize(axisAngle(axis, travel * 0.012f) * transform->rotation);
    } else {
        transform->scale[i] = std::max(0.01f, transform->scale[i] * (1.0f + travel * 0.01f));
    }
}
```

```cpp
/// Called at the end of every frame. When an edit has just been finished, the scene as
/// it was before becomes the next thing Undo goes back to.
void Editor::recordUndo(Engine& engine) {
    if (!touched_ || isPlaying_ || gui_.isBusy() || dragAxis_ >= 0) return;
    touched_ = false;
    std::string state = writeScene(engine.scene, materials_, engine.renderer().settings);
    if (state == current_) return;
    undo_.push_back(std::move(current_));
    if (undo_.size() > kUndoLevels) undo_.erase(undo_.begin());
    redo_.clear();
    current_ = std::move(state);
}
```

```cpp
/// Play runs the scene: physics starts and the scene's own camera takes over. Stop puts
/// everything back exactly as it was, from the text the scene was saved to in memory.
void Editor::setPlaying(Engine& engine, bool playing) {
    if (playing == isPlaying_) return;
    if (playing) {
        beforePlay_ = writeScene(engine.scene, materials_, engine.renderer().settings);
        isPlaying_ = true;
        engine.physics.reset();
        // Without a camera of its own the scene is watched through the editor's.
        bool hasCamera = false;
        engine.scene.each<Camera>([&](Entity entity, Camera& camera) {
            hasCamera = hasCamera || (entity != camera_ && camera.isActive);
        });
        engine.renderer().cameraOverride = hasCamera ? Entity{} : camera_;
        if (Camera* own = engine.scene.get<Camera>(camera_)) own->isActive = !hasCamera;
        engine.isSimulationPaused = false;
        say("Playing. Press F5 or Stop to go back to editing");
    } else {
        isPlaying_ = false;
        engine.isSimulationPaused = true;
        restore(engine, beforePlay_);
        say("Stopped");
    }
}
```
