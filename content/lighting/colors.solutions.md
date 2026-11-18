Multiply channel by channel. A light of (0.33, 0.42, 0.18) on the coral object (1.0, 0.5, 0.31) gives (0.33, 0.21, 0.06), a dark olive. A pure blue light gives (0, 0, 0.31): the object looks dark blue, because blue is the only light it can reflect.
---
Set the light color each frame, for example in Swift `Float3(sin(time * 2.0), sin(time * 0.7), sin(time * 1.3)) * 0.5 + 0.5`. The `* 0.5 + 0.5` keeps each channel between 0 and 1. Use the same value for the lamp cube's color so the lamp matches the light it casts.
