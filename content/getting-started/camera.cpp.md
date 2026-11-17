```cpp
/// Right-handed view matrix.
inline simd::float4x4 lookAt(simd::float3 eye, simd::float3 center, simd::float3 up) {
    simd::float3 z = simd::normalize(eye - center);        // points backward, away from the target
    simd::float3 x = simd::normalize(simd::cross(up, z));  // right
    simd::float3 y = simd::cross(z, x);                    // true up
    return simd_matrix(simd_make_float4(x.x, y.x, z.x, 0),
                       simd_make_float4(x.y, y.y, z.y, 0),
                       simd_make_float4(x.z, y.z, z.z, 0),
                       simd_make_float4(-simd::dot(x, eye), -simd::dot(y, eye), -simd::dot(z, eye), 1));
}
```

```cpp
float radius = 10.0f;
simd::float3 eye = {std::sin(time) * radius, 0, std::cos(time) * radius};
uniforms.view = lookAt(eye, simd::float3{0, 0, 0}, simd::float3{0, 1, 0});
```

```cpp
#include <algorithm>
#include "Math.hpp"

class Camera {
public:
    simd::float3 position = {0, 0, 3};
    float yaw = -90;      // degrees; -90 looks down -z
    float pitch = 0;
    float fov = 45;

    float speed = 2.5f;
    float sensitivity = 0.1f;

    simd::float3 front() const {
        float y = radians(yaw), p = radians(pitch);
        return simd::normalize(simd::float3{std::cos(y) * std::cos(p), std::sin(p), std::sin(y) * std::cos(p)});
    }
    simd::float3 right() const { return simd::normalize(simd::cross(front(), simd::float3{0, 1, 0})); }

    simd::float4x4 viewMatrix() const {
        return lookAt(position, position + front(), simd::float3{0, 1, 0});
    }

    void move(float forward, float strafe, float deltaTime) {
        position += front() * forward * speed * deltaTime;
        position += right() * strafe * speed * deltaTime;
    }

    void rotate(float deltaX, float deltaY) {
        yaw += deltaX * sensitivity;
        pitch = std::clamp(pitch + deltaY * sensitivity, -89.0f, 89.0f);
    }

    void zoom(float amount) {
        fov = std::clamp(fov - amount, 1.0f, 60.0f);
    }
};
```

```cpp
double lastFrameTime = glfwGetTime();

// in draw()
double now = glfwGetTime();
float deltaTime = float(now - lastFrameTime);
lastFrameTime = now;
```

```cpp
// GLFW lets you poll the keyboard directly.
void updateCamera(GLFWwindow* window, Camera& camera, float deltaTime) {
    float forward = 0, strafe = 0;
    if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS) forward += 1;
    if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS) forward -= 1;
    if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS) strafe += 1;
    if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS) strafe -= 1;
    camera.move(forward, strafe, deltaTime);
}
```

```cpp
// Mouse movement and scrolling arrive through callbacks. Register them once after creating the window.
glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);    // capture the cursor
glfwSetWindowUserPointer(window, &camera);

glfwSetCursorPosCallback(window, [](GLFWwindow* w, double x, double y) {
    static double lastX = x, lastY = y;
    auto* camera = static_cast<Camera*>(glfwGetWindowUserPointer(w));
    camera->rotate(float(x - lastX), float(lastY - y));         // window y grows downward
    lastX = x;
    lastY = y;
});
glfwSetScrollCallback(window, [](GLFWwindow* w, double, double yOffset) {
    static_cast<Camera*>(glfwGetWindowUserPointer(w))->zoom(float(yOffset));
});
```

```cpp
Camera camera;

// in draw()
updateCamera(window, camera, deltaTime);
uniforms.view = camera.viewMatrix();
uniforms.projection = perspective(radians(camera.fov), aspect, 0.1f, 100.0f);
```
