# Multiple Lights

A scene rarely has one light. This chapter combines everything from the lighting section: one directional light, four point lights and a flashlight, all in a single fragment function. The trick is organization: one function per light type, and their results added together.

## Shader functions

MSL is C++, so ordinary helper functions work. Anything not marked `vertex`, `fragment` or `kernel` is a plain function you can call. Mark helpers `static` so they stay private to the file.

```cpp
struct Surface {
    float3 position;
    float3 normal;
    float3 viewDir;
    float3 albedo;
    float3 specular;
    float shininess;
};

static float3 calcDirectionalLight(DirectionalLight light, Surface s) {
    float3 lightDir = normalize(-light.direction);
    float diff = max(dot(s.normal, lightDir), 0.0);
    float spec = pow(max(dot(s.viewDir, reflect(-lightDir, s.normal)), 0.0), s.shininess);

    return light.ambient * s.albedo
         + light.diffuse * diff * s.albedo
         + light.specular * spec * s.specular;
}

static float3 calcPointLight(PointLight light, Surface s) {
    float3 toLight = light.position - s.position;
    float distance = length(toLight);
    float3 lightDir = toLight / distance;

    float diff = max(dot(s.normal, lightDir), 0.0);
    float spec = pow(max(dot(s.viewDir, reflect(-lightDir, s.normal)), 0.0), s.shininess);
    float attenuation = 1.0 / (light.constantTerm
                             + light.linearTerm * distance
                             + light.quadraticTerm * distance * distance);

    return (light.ambient * s.albedo
          + light.diffuse * diff * s.albedo
          + light.specular * spec * s.specular) * attenuation;
}
```

`calcSpotLight` is the point light function with the cone intensity from the previous chapter multiplied into the diffuse and specular terms.

Collecting the surface properties in a `Surface` struct keeps the parameter lists short and means textures are sampled once, not once per light.

## Arrays in uniforms

A fixed-size array inside the uniform struct holds the point lights:

```cpp
#define POINT_LIGHT_COUNT 4

struct FragmentUniforms {
    DirectionalLight directionalLight;
    PointLight pointLights[POINT_LIGHT_COUNT];
    SpotLight spotLight;
    float3 viewPosition;
    float shininess;
};
```

```cpp
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> diffuseMap  [[texture(0)]],
                              texture2d<float> specularMap [[texture(1)]],
                              sampler mapSampler [[sampler(0)]]) {
    Surface s;
    s.position = in.worldPosition;
    s.normal = normalize(in.normal);
    s.viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    s.albedo = diffuseMap.sample(mapSampler, in.uv).rgb;
    s.specular = specularMap.sample(mapSampler, in.uv).rgb;
    s.shininess = uniforms.shininess;

    float3 color = calcDirectionalLight(uniforms.directionalLight, s);
    for (int i = 0; i < POINT_LIGHT_COUNT; i++) {
        color += calcPointLight(uniforms.pointLights[i], s);
    }
    color += calcSpotLight(uniforms.spotLight, s);

    return float4(color, 1.0);
}
```

## The Swift side

Swift has no fixed-size C arrays in structs, but a **tuple** of identical elements has the same memory layout:

```swift
struct FragmentUniforms {
    var directionalLight: DirectionalLight
    var pointLights: (PointLight, PointLight, PointLight, PointLight)
    var spotLight: SpotLight
    var viewPosition: Float3
    var shininess: Float
}
```

That gets clumsy for larger counts. The scalable alternative is to put the lights in their own `MTLBuffer` and pass a pointer plus a count:

```cpp
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              constant PointLight *pointLights [[buffer(2)]],
                              ...) {
    for (uint i = 0; i < uniforms.pointLightCount; i++) {
        color += calcPointLight(pointLights[i], s);
    }
```

```swift
let lightBuffer = device.makeBuffer(bytes: pointLights,
                                    length: MemoryLayout<PointLight>.stride * pointLights.count,
                                    options: [])!
encoder.setFragmentBuffer(lightBuffer, offset: 0, index: 2)
```

A buffer bound to a shader is just memory, and a pointer parameter lets the shader index it as an array of any length. This is far more flexible than uniform arrays in older APIs, and it is the form we use from now on.

## Setting the scene

Four point lights at different positions, each drawn as a small lamp cube with the unlit pipeline from the [Colors](colors.html) chapter:

```swift
let pointLightPositions: [Float3] = [
    [ 0.7,  0.2,   2.0],
    [ 2.3, -3.3,  -4.0],
    [-4.0,  2.0, -12.0],
    [ 0.0,  0.0,  -3.0],
]
```

## The cost of many lights

Every fragment evaluates every light, so the cost is fragments × lights. A handful is fine. Hundreds are not, and solving that is the purpose of [Deferred Shading](../advanced-lighting/deferred-shading.html) later on.

## Exercises

- Recreate different atmospheres only by changing light colors and the clear color: a desert at noon, a dim factory, a horror corridor lit by the flashlight alone.
- Move the lights over time by rewriting the buffer contents each frame through `lightBuffer.contents()`.
