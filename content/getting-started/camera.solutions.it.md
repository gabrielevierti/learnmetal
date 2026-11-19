Muoviti lungo un vettore front appiattito, così guardare in alto o in basso non cambia la tua altezza: normalizza `(front.x, 0, front.z)` e usa quello in `move`. Lascia invariata `viewMatrix`, così puoi ancora guardarti intorno liberamente.
---
Aggiungi a `move` un input verticale e applicalo lungo l'asse up del mondo: `position.y += vertical * speed * deltaTime`. Leggi i due tasti come fai con W e S (`.keyQ` e `.keyE` con GameController, `GLFW_KEY_Q` e `GLFW_KEY_E` con GLFW).
---
Moltiplica la velocità finché Shift è premuto. Con GameController controlla `keyboard.button(forKeyCode: .leftShift)?.isPressed`; con GLFW controlla `glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS`. Poi passa `deltaTime * 3` a `move`, oppure scala `speed` per quel frame.
