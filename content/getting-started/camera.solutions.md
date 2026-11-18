Move along a flattened front vector, so looking up or down does not change your height: normalize `(front.x, 0, front.z)` and use that in `move`. Leave `viewMatrix` unchanged so you can still look around freely.
---
Add a vertical input to `move` and apply it along the world up axis: `position.y += vertical * speed * deltaTime`. Read the two keys the same way as W and S (`.keyQ` and `.keyE` with GameController, `GLFW_KEY_Q` and `GLFW_KEY_E` with GLFW).
---
Multiply the speed while Shift is down. With GameController check `keyboard.button(forKeyCode: .leftShift)?.isPressed`; with GLFW check `glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS`. Then pass `deltaTime * 3` to `move`, or scale `speed` for that frame.
