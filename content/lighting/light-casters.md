# Light Casters

Until now the light has been a single point shining equally in all directions forever. Real scenes have three common kinds of light source: directional lights, point lights and spotlights.

## Directional light

A light that is extremely far away, like the sun, has rays that are effectively parallel. Its position is irrelevant; only its **direction** matters, and it is the same for every fragment.

```cpp
struct DirectionalLight {
    float3 direction;   // the direction the light travels
    float3 ambient;
    float3 diffuse;
    float3 specular;
};
```

The lighting math wants a vector from the fragment *toward* the light, so negate it:

```cpp
float3 lightDir = normalize(-light.direction);
```

Everything else stays the same. With `direction = (-0.2, -1.0, -0.3)` all ten cubes are lit from above at the same angle.

## Point light

A point light has a position and shines in all directions, but it fades with distance. That fading is called **attenuation**. A formula that looks good and is cheap:

```
attenuation = 1 / (constant + linear * d + quadratic * d²)
```

where `d` is the distance from the light. The constant term is normally 1 so the result never exceeds 1. The linear and quadratic terms set how fast the light dies off.

| Range | Constant | Linear | Quadratic |
| --- | --- | --- | --- |
| 13 | 1.0 | 0.35 | 0.44 |
| 50 | 1.0 | 0.09 | 0.032 |
| 100 | 1.0 | 0.045 | 0.0075 |
| 325 | 1.0 | 0.014 | 0.0007 |

```cpp
struct PointLight {
    float3 position;
    float3 ambient;
    float3 diffuse;
    float3 specular;
    float constantTerm;
    float linearTerm;
    float quadraticTerm;
};
```

```cpp
float distance = length(light.position - in.worldPosition);
float attenuation = 1.0 / (light.constantTerm
                         + light.linearTerm * distance
                         + light.quadraticTerm * distance * distance);

ambient  *= attenuation;
diffuse  *= attenuation;
specular *= attenuation;
```

## Spotlight

A spotlight is a point light that only shines inside a cone. It needs a position, a direction, and a **cutoff** angle. For each fragment, compare the angle between the spotlight's direction and the direction from the light to the fragment against the cutoff.

Comparing angles would require an expensive inverse cosine, so we compare cosines instead. Pass the cosine of the cutoff from Swift:

```swift
light.cutOff = cos(Float(12.5).radians)
light.outerCutOff = cos(Float(17.5).radians)
```

A hard cutoff gives an ugly sharp circle. Two cones, an inner and a slightly larger outer one, give a soft edge: full brightness inside the inner cone, none outside the outer cone, and a smooth blend between.

```cpp
struct SpotLight {
    float3 position;
    float3 direction;
    float3 ambient;
    float3 diffuse;
    float3 specular;
    float cutOff;        // cosine of the inner angle
    float outerCutOff;   // cosine of the outer angle
};
```

```cpp
float3 lightDir = normalize(light.position - in.worldPosition);
float theta = dot(lightDir, normalize(-light.direction));
float epsilon = light.cutOff - light.outerCutOff;
float intensity = saturate((theta - light.outerCutOff) / epsilon);

diffuse  *= intensity;
specular *= intensity;
```

`saturate(x)` clamps to the 0 to 1 range. Ambient is left alone so that the scene outside the cone is not pitch black. Remember that a *larger* cosine means a *smaller* angle, which is why the comparison looks reversed.

## A flashlight

A flashlight is a spotlight attached to the camera:

```swift
light.position = camera.position
light.direction = camera.front
```

Add attenuation as well and walk around the cubes in the dark.

## Exercises

- Give the directional light a warm color and a low angle for a sunset.
- Experiment with the attenuation terms until a point light reaches exactly the nearest cubes.
- Project a texture from the spotlight, like a slide projector: use the fragment's position within the cone as a texture coordinate.
