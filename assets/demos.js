/* Live demo definitions for learnmetal. Shader code is Metal Shading Language; see live.js. */
(function () {
  "use strict";
  const LM = window.LM, M = LM.math;
  const rad = (d) => (d * Math.PI) / 180;

  const CUBES = [[0, 0, 0], [2, 5, -15], [-1.5, -2.2, -2.5], [-3.8, -2, -12.3], [2.4, -0.4, -3.5],
    [-1.7, 3, -7.5], [1.3, -2, -2.5], [1.5, 2, -2.5], [1.5, 0.2, -1.5], [-1.3, 1, -1.5]];
  const tenCubes = (t) => CUBES.map((p, i) => ({
    mesh: "cube",
    model: M.mul(M.translate(p[0], p[1], p[2]), M.rotate(rad(20 * i) + (i % 3 === 0 ? t * 0.6 : 0), 1, 0.3, 0.5)),
  }));
  const lamp = (p, color, s) => ({ mesh: "cube", lamp: color || [1, 1, 1], model: M.mul(M.translate(p[0], p[1], p[2]), M.scale(s || 0.16)) });
  const orbit = (t, r, y, speed) => [Math.cos(t * (speed || 0.8)) * r, y, Math.sin(t * (speed || 0.8)) * r];
  const floor = (y, size, tex) => ({ mesh: "floor", model: M.mul(M.translate(0, y, 0), M.scale(size, 1, size)), textures: tex });

  // ---------------------------------------------------------------- shared shader text

  const LIT = `
struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
    float2 uv       [[attribute(2)]];
};

struct Uniforms {
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float3x3 normalMatrix;
};

struct VertexOut {
    float4 position [[position]];
    float3 worldPosition;
    float3 normal;
    float2 uv;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    float4 world = uniforms.model * float4(in.position, 1.0);
    out.position = uniforms.projection * uniforms.view * world;
    out.worldPosition = world.xyz;
    out.normal = uniforms.normalMatrix * in.normal;
    out.uv = in.uv;
    return out;
}`;

  const SCREEN = `
struct ScreenOut {
    float4 position [[position]];
    float2 uv;
};

// One oversized triangle that covers the screen. No vertex buffer needed.
vertex ScreenOut vertex_fullscreen(uint vertexID [[vertex_id]]) {
    float2 uv = float2(float((vertexID << 1) & 2u), float(vertexID & 2u));
    ScreenOut out;
    out.position = float4(uv * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
    out.uv = uv;
    return out;
}`;

  const SKY = `
// A procedural sky standing in for a cubemap: sample it with a direction.
static float3 sky(float3 d) {
    float3 color = mix(float3(0.78, 0.86, 0.98), float3(0.16, 0.36, 0.80), pow(saturate(d.y), 0.55));
    float sun = saturate(dot(d, normalize(float3(0.55, 0.42, -0.6))));
    color += float3(1.0, 0.9, 0.7) * (pow(sun, 30.0) * 0.5 + pow(sun, 900.0) * 4.0);
    if (d.y < 0.0) {
        float2 g = d.xz / -d.y;
        float checker = fmod(floor(g.x * 1.2) + floor(g.y * 1.2), 2.0);
        float3 ground = mix(float3(0.50, 0.47, 0.42), float3(0.30, 0.28, 0.26), abs(checker));
        color = mix(float3(0.42, 0.44, 0.40), ground, saturate(-d.y * 3.5));
    }
    return color;
}`;

  // ---------------------------------------------------------------- getting started

  LM.define("hello-view", {
    caption: "Change the clear color. This is all the first renderer does: clear, present, repeat.",
    controls: [{ id: "color", type: "color", label: "clearColor", value: "#334d4d" }],
    clear: (s) => s.color,
    animate: false, editable: false, camera: { mode: "fixed" },
    code: SCREEN + "\nfragment float4 fragment_main(ScreenOut in [[stage_in]]) { return float4(0.0); }",
    objects: () => [],
  });

  LM.define("hello-triangle", {
    caption: "Edit the positions or the color. The shader recompiles as you type.",
    aspect: 1, maxWidth: 440, animate: false, camera: { mode: "fixed" },
    clear: () => [0.2, 0.3, 0.3],
    objects: () => [{ mesh: "triangle", model: M.ident() }],
    code: `
struct VertexIn {
    float3 position [[attribute(0)]];
};

struct VertexOut {
    float4 position [[position]];
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]]) {
    VertexOut out;
    out.position = float4(in.position, 1.0);
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]]) {
    return float4(1.0, 0.5, 0.2, 1.0);
}`,
  });

  LM.define("shaders", {
    caption: "Per-vertex colors are interpolated across the triangle. Try out.color = out.position.",
    aspect: 1, maxWidth: 440, camera: { mode: "fixed" },
    clear: () => [0.2, 0.3, 0.3],
    objects: () => [{ mesh: "triangle", model: M.ident() }],
    code: `
struct VertexIn {
    float3 position [[attribute(0)]];
    float3 color    [[attribute(3)]];
};

struct VertexOut {
    float4 position [[position]];
    float4 color;
};

struct Uniforms {
    float time;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]]) {
    VertexOut out;
    out.position = float4(in.position, 1.0);
    out.color = float4(in.color, 1.0);
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant Uniforms &uniforms [[buffer(0)]]) {
    float pulse = sin(uniforms.time * 2.0) * 0.25 + 0.75;
    return in.color * pulse;
}`,
  });

  LM.define("textures", {
    caption: "Raise the UV scale above 1 to see the address modes, and switch the filter to nearest to see texels.",
    aspect: 1, maxWidth: 440, animate: false, camera: { mode: "fixed" },
    clear: () => [0.2, 0.3, 0.3],
    textures: { texture0: "crate", texture1: "face" },
    controls: [
      { id: "mix", label: "mix factor", min: 0, max: 1, value: 0.2 },
      { id: "scale", label: "UV scale", min: 0.2, max: 4, value: 1 },
      { id: "wrap", type: "select", label: "address mode", value: "repeat", options: [["repeat", ".repeat"], ["mirror", ".mirrorRepeat"], ["clamp", ".clampToEdge"]] },
      { id: "filter", type: "select", label: "filter", value: "linear", options: [["linear", ".linear"], ["nearest", ".nearest"]] },
    ],
    sampler: (s) => ({ wrap: s.wrap, filter: s.filter }),
    uniforms: (s) => ({ mixFactor: s.mix, uvScale: s.scale }),
    objects: () => [{ mesh: "quad", model: M.scale(1.6) }],
    code: `
struct VertexIn {
    float3 position [[attribute(0)]];
    float2 uv       [[attribute(2)]];
};

struct VertexOut {
    float4 position [[position]];
    float2 uv;
};

struct Uniforms {
    float4x4 model;
    float mixFactor;
    float uvScale;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    out.position = uniforms.model * float4(in.position, 1.0);
    out.uv = (in.uv - 0.5) * uniforms.uvScale + 0.5;
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant Uniforms &uniforms [[buffer(1)]],
                              texture2d<float> texture0 [[texture(0)]],
                              texture2d<float> texture1 [[texture(1)]],
                              sampler textureSampler [[sampler(0)]]) {
    float4 a = texture0.sample(textureSampler, in.uv);
    float4 b = texture1.sample(textureSampler, in.uv);
    return mix(a, b, uniforms.mixFactor);
}`,
  });

  LM.define("transformations", {
    caption: "Move the sliders, then switch the order: rotating after translating swings the quad around the origin.",
    aspect: 1, maxWidth: 440, animate: false, camera: { mode: "fixed" },
    clear: () => [0.2, 0.3, 0.3],
    textures: { colorTexture: "crate" },
    controls: [
      { id: "tx", label: "translate x", min: -1, max: 1, value: 0.4 },
      { id: "ty", label: "translate y", min: -1, max: 1, value: -0.3 },
      { id: "angle", label: "rotate (degrees)", min: -180, max: 180, step: 1, value: 30 },
      { id: "scale", label: "scale", min: 0.1, max: 2, value: 0.6 },
      { id: "order", type: "select", label: "order", value: "trs", options: [["trs", "translate * rotate * scale"], ["rts", "rotate * translate * scale"]] },
    ],
    uniforms: (s) => {
      const T = M.translate(s.tx, s.ty, 0), R = M.rotate(rad(s.angle), 0, 0, 1), S = M.scale(s.scale);
      return { transform: s.order === "trs" ? M.chain(T, R, S) : M.chain(R, T, S) };
    },
    objects: () => [{ mesh: "quad", model: M.ident() }],
    code: `
struct VertexIn {
    float3 position [[attribute(0)]];
    float2 uv       [[attribute(2)]];
};

struct VertexOut {
    float4 position [[position]];
    float2 uv;
};

struct Uniforms {
    float4x4 transform;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    out.position = uniforms.transform * float4(in.position, 1.0);
    out.uv = in.uv;
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              texture2d<float> colorTexture [[texture(0)]],
                              sampler textureSampler [[sampler(0)]]) {
    return colorTexture.sample(textureSampler, in.uv);
}`,
  });

  const TEXTURED = `
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              texture2d<float> colorTexture [[texture(0)]],
                              sampler textureSampler [[sampler(0)]]) {
    return colorTexture.sample(textureSampler, in.uv);
}`;

  LM.define("coordinate-systems", {
    caption: "Turn the depth test off to see faces drawn in submission order, and change the field of view.",
    clear: () => [0.2, 0.3, 0.3], camera: { eye: [0, 0, 3], mode: "fixed" },
    textures: { colorTexture: "crate" },
    controls: [
      { id: "fov", label: "field of view", min: 15, max: 100, step: 1, value: 45 },
      { id: "depth", type: "check", label: "depth test", value: true },
    ],
    fov: (s) => s.fov,
    state: (s) => ({ depth: s.depth }),
    objects: (s, t) => tenCubes(t),
    prelude: LIT, code: TEXTURED,
  });

  LM.define("camera", {
    caption: "Click the view, then fly with W A S D (Q and E for down and up) and drag to look around.",
    clear: () => [0.2, 0.3, 0.3], camera: { eye: [0, 0, 3], target: [0, 0, 0], mode: "fly" },
    textures: { colorTexture: "crate" },
    state: () => ({ cull: "back" }),
    objects: (s, t) => tenCubes(0),
    prelude: LIT, code: TEXTURED, editable: false,
  });

  // ---------------------------------------------------------------- lighting

  LM.define("colors", {
    caption: "The color you see is the light's color multiplied by the object's color.",
    camera: { eye: [-1.6, 1.3, 3.4], target: [0.3, 0.1, 0.3] }, animate: false,
    controls: [
      { id: "light", type: "color", label: "lightColor", value: "#ffffff" },
      { id: "object", type: "color", label: "objectColor", value: "#ff804f" },
    ],
    uniforms: (s) => ({ lightColor: s.light, objectColor: s.object }),
    objects: (s) => [{ mesh: "cube", model: M.ident() }, lamp([1.2, 1.0, 2.0], s.light, 0.2)],
    prelude: LIT,
    code: `
struct FragmentUniforms {
    float3 objectColor;
    float3 lightColor;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]]) {
    return float4(uniforms.lightColor * uniforms.objectColor, 1.0);
}`,
  });

  LM.define("basic-lighting", {
    caption: "Drag to orbit. Set a strength to zero to see what each term contributes.",
    camera: { eye: [1.9, 1.3, 2.9], target: [0, 0, 0] },
    controls: [
      { id: "ambient", label: "ambient", min: 0, max: 1, value: 0.1 },
      { id: "specular", label: "specular", min: 0, max: 1, value: 0.5 },
      { id: "shininess", label: "shininess", min: 2, max: 256, step: 1, value: 32 },
    ],
    uniforms: (s, t) => ({ objectColor: [1, 0.5, 0.31], lightColor: [1, 1, 1], lightPosition: orbit(t, 2, 1),
      ambientStrength: s.ambient, specularStrength: s.specular, shininess: s.shininess }),
    objects: (s, t) => [{ mesh: "cube", model: M.ident() }, lamp(orbit(t, 2, 1))],
    prelude: LIT,
    code: `
struct FragmentUniforms {
    float3 objectColor;
    float3 lightColor;
    float3 lightPosition;
    float3 viewPosition;
    float ambientStrength;
    float specularStrength;
    float shininess;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]]) {
    float3 normal = normalize(in.normal);
    float3 lightDir = normalize(uniforms.lightPosition - in.worldPosition);

    float3 ambient = uniforms.ambientStrength * uniforms.lightColor;

    float diff = max(dot(normal, lightDir), 0.0);
    float3 diffuse = diff * uniforms.lightColor;

    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    float3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), uniforms.shininess);
    float3 specular = uniforms.specularStrength * spec * uniforms.lightColor;

    return float4((ambient + diffuse + specular) * uniforms.objectColor, 1.0);
}`,
  });

  const MATERIALS = {
    coral: [[1.0, 0.5, 0.31], [1.0, 0.5, 0.31], [0.5, 0.5, 0.5], 32],
    emerald: [[0.02, 0.17, 0.02], [0.08, 0.61, 0.08], [0.63, 0.73, 0.63], 77],
    gold: [[0.25, 0.2, 0.07], [0.75, 0.61, 0.23], [0.63, 0.56, 0.37], 51],
    plastic: [[0.0, 0.1, 0.06], [0.0, 0.51, 0.51], [0.5, 0.5, 0.5], 32],
    rubber: [[0.05, 0.0, 0.0], [0.5, 0.4, 0.4], [0.7, 0.04, 0.04], 10],
  };
  LM.define("materials", {
    caption: "The same cube and the same light. Only the four material values change.",
    camera: { eye: [1.9, 1.3, 2.9], target: [0, 0, 0] },
    controls: [{ id: "m", type: "select", label: "material", value: "coral",
      options: [["coral", "Coral"], ["emerald", "Emerald"], ["gold", "Gold"], ["plastic", "Cyan plastic"], ["rubber", "Red rubber"]] }],
    uniforms: (s, t) => {
      const m = MATERIALS[s.m];
      return { "material.ambient": m[0], "material.diffuse": m[1], "material.specular": m[2], "material.shininess": m[3],
        "light.position": orbit(t, 2, 1), "light.ambient": [0.25, 0.25, 0.25], "light.diffuse": [0.8, 0.8, 0.8], "light.specular": [1, 1, 1] };
    },
    objects: (s, t) => [{ mesh: "cube", model: M.ident() }, lamp(orbit(t, 2, 1))],
    prelude: LIT,
    code: `
struct Material {
    float3 ambient;
    float3 diffuse;
    float3 specular;
    float shininess;
};

struct Light {
    float3 position;
    float3 ambient;
    float3 diffuse;
    float3 specular;
};

struct FragmentUniforms {
    Material material;
    Light light;
    float3 viewPosition;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]]) {
    Material material = uniforms.material;
    Light light = uniforms.light;

    float3 normal = normalize(in.normal);
    float3 lightDir = normalize(light.position - in.worldPosition);
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    float3 reflectDir = reflect(-lightDir, normal);

    float3 ambient = light.ambient * material.ambient;
    float3 diffuse = light.diffuse * (max(dot(normal, lightDir), 0.0) * material.diffuse);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);
    float3 specular = light.specular * (spec * material.specular);

    return float4(ambient + diffuse + specular, 1.0);
}`,
  });

  LM.define("lighting-maps", {
    caption: "With the specular map only the steel frame shines. Untick it to give the wood the same highlight.",
    camera: { eye: [1.6, 1.1, 2.5], target: [0, 0, 0] },
    textures: { diffuseMap: "crate", specularMap: "crateSpec" },
    controls: [{ id: "spec", type: "check", label: "use the specular map", value: true }],
    uniforms: (s, t) => ({ lightPosition: orbit(t, 1.7, 0.8), shininess: 64, useSpecularMap: s.spec ? 1 : 0 }),
    objects: (s, t) => [{ mesh: "cube", model: M.ident() }, lamp(orbit(t, 1.7, 0.8), null, 0.12)],
    prelude: LIT,
    code: `
struct FragmentUniforms {
    float3 lightPosition;
    float3 viewPosition;
    float shininess;
    int useSpecularMap;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> diffuseMap  [[texture(0)]],
                              texture2d<float> specularMap [[texture(1)]],
                              sampler mapSampler [[sampler(0)]]) {
    float3 albedo = diffuseMap.sample(mapSampler, in.uv).rgb;
    float3 specularColor = uniforms.useSpecularMap != 0
        ? specularMap.sample(mapSampler, in.uv).rgb
        : float3(0.5);

    float3 normal = normalize(in.normal);
    float3 lightDir = normalize(uniforms.lightPosition - in.worldPosition);
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    float3 reflectDir = reflect(-lightDir, normal);

    float3 ambient = 0.2 * albedo;
    float3 diffuse = max(dot(normal, lightDir), 0.0) * albedo;
    float3 specular = pow(max(dot(viewDir, reflectDir), 0.0), uniforms.shininess) * specularColor;

    return float4(ambient + diffuse + specular, 1.0);
}`,
  });

  LM.define("light-casters", {
    caption: "Switch the kind of light. The spotlight is a flashlight attached to the camera: drag to aim it.",
    camera: { eye: [0, 0, 3.6], target: [0, 0, -1.5] }, clear: () => [0.04, 0.04, 0.05], animate: false,
    textures: { diffuseMap: "crate", specularMap: "crateSpec" },
    controls: [
      { id: "kind", type: "select", label: "light", value: "2", options: [["0", "Directional"], ["1", "Point"], ["2", "Spot"]] },
      { id: "cut", label: "spot inner angle", min: 3, max: 30, step: 0.5, value: 12.5 },
      { id: "soft", label: "spot soft edge", min: 0, max: 15, step: 0.5, value: 5 },
    ],
    uniforms: (s, t, b) => ({ kind: +s.kind, lightPosition: s.kind === "2" ? b.viewPosition : [1.2, 1.0, 2.0],
      lightDirection: s.kind === "2" ? b.cameraFront : [-0.2, -1.0, -0.3],
      cutOff: Math.cos(rad(s.cut)), outerCutOff: Math.cos(rad(s.cut + s.soft + 0.01)) }),
    objects: (s) => tenCubes(0).concat(s.kind === "1" ? [lamp([1.2, 1.0, 2.0])] : []),
    prelude: LIT,
    code: `
struct FragmentUniforms {
    float3 viewPosition;
    float3 lightPosition;
    float3 lightDirection;   // the direction the light travels
    float cutOff;            // cosine of the inner angle
    float outerCutOff;       // cosine of the outer angle
    int kind;                // 0 directional, 1 point, 2 spot
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> diffuseMap  [[texture(0)]],
                              texture2d<float> specularMap [[texture(1)]],
                              sampler mapSampler [[sampler(0)]]) {
    float3 albedo = diffuseMap.sample(mapSampler, in.uv).rgb;
    float3 normal = normalize(in.normal);
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);

    float3 lightDir = normalize(-uniforms.lightDirection);
    float intensity = 1.0;

    if (uniforms.kind != 0) {
        float3 toLight = uniforms.lightPosition - in.worldPosition;
        float distance = length(toLight);
        lightDir = toLight / distance;
        intensity = 1.0 / (1.0 + 0.09 * distance + 0.032 * distance * distance);
    }
    if (uniforms.kind == 2) {
        float theta = dot(lightDir, normalize(-uniforms.lightDirection));
        float epsilon = uniforms.cutOff - uniforms.outerCutOff;
        intensity *= saturate((theta - uniforms.outerCutOff) / epsilon);
    }

    float diff = max(dot(normal, lightDir), 0.0);
    float spec = pow(max(dot(viewDir, reflect(-lightDir, normal)), 0.0), 32.0);
    float3 specular = spec * specularMap.sample(mapSampler, in.uv).rgb;

    return float4(0.08 * albedo + (diff * albedo + specular) * intensity, 1.0);
}`,
  });

  const POINTS = [[[0.7, 0.2, 2.0], [1.0, 0.6, 0.3]], [[2.3, -3.3, -4.0], [0.4, 0.6, 1.0]],
    [[-4.0, 2.0, -12.0], [0.5, 1.0, 0.5]], [[0.0, 0.0, -3.0], [1.0, 0.4, 0.5]]];
  LM.define("multiple-lights", {
    caption: "A directional light and four colored point lights in one fragment function. Drag to look around.",
    camera: { eye: [0, 0, 4.5], target: [0, 0, -1.5] }, clear: () => [0.04, 0.04, 0.06], animate: false,
    textures: { diffuseMap: "crate", specularMap: "crateSpec" },
    uniforms: () => {
      const u = { sunDirection: [-0.2, -1.0, -0.3], sunColor: [0.35, 0.35, 0.4], pointLightCount: 4 };
      POINTS.forEach((p, i) => { u["pointLights[" + i + "].position"] = p[0]; u["pointLights[" + i + "].color"] = p[1]; });
      return u;
    },
    objects: () => tenCubes(0).concat(POINTS.map((p) => lamp(p[0], p[1], 0.14))),
    prelude: LIT,
    code: `
struct PointLight {
    float3 position;
    float3 color;
};

struct FragmentUniforms {
    float3 viewPosition;
    float3 sunDirection;
    float3 sunColor;
    int pointLightCount;
};

struct Surface {
    float3 position;
    float3 normal;
    float3 viewDir;
    float3 albedo;
    float3 specular;
};

// Diffuse + specular for one light direction, without ambient.
static float3 phong(Surface s, float3 lightDir, float3 lightColor) {
    float diff = max(dot(s.normal, lightDir), 0.0);
    float spec = pow(max(dot(s.viewDir, reflect(-lightDir, s.normal)), 0.0), 32.0);
    return (diff * s.albedo + spec * s.specular) * lightColor;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              constant PointLight *pointLights [[buffer(2)]],
                              texture2d<float> diffuseMap  [[texture(0)]],
                              texture2d<float> specularMap [[texture(1)]],
                              sampler mapSampler [[sampler(0)]]) {
    Surface s;
    s.position = in.worldPosition;
    s.normal = normalize(in.normal);
    s.viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    s.albedo = diffuseMap.sample(mapSampler, in.uv).rgb;
    s.specular = specularMap.sample(mapSampler, in.uv).rgb;

    float3 color = 0.06 * s.albedo;
    color += phong(s, normalize(-uniforms.sunDirection), uniforms.sunColor);

    for (int i = 0; i < uniforms.pointLightCount; i++) {
        float3 toLight = pointLights[i].position - s.position;
        float distance = length(toLight);
        float attenuation = 1.0 / (1.0 + 0.09 * distance + 0.032 * distance * distance);
        color += phong(s, toLight / distance, pointLights[i].color) * attenuation;
    }
    return float4(color, 1.0);
}`,
  });

  // ---------------------------------------------------------------- advanced metal

  LM.define("depth-testing", {
    caption: "Raw depth is almost white everywhere. Linearized, it becomes a readable distance.",
    camera: { eye: [0, 0, 3], target: [0, 0, -1.5] }, animate: false,
    controls: [{ id: "linear", type: "check", label: "linearize", value: false }],
    uniforms: (s) => ({ linearize: s.linear ? 1 : 0 }),
    objects: () => tenCubes(0).concat([floor(-3.2, 60)]),
    prelude: LIT,
    code: `
struct FragmentUniforms {
    int linearize;
};

static float linearizeDepth(float depth, float near, float far) {
    return near * far / (far - depth * (far - near));
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]]) {
    // in.position.z is the value written to the depth buffer.
    float depth = in.position.z;
    if (uniforms.linearize != 0) {
        depth = linearizeDepth(depth, 0.1, 100.0) / 25.0;
    }
    return float4(float3(depth), 1.0);
}`,
  });

  LM.define("face-culling", {
    caption: "Front faces are green and back faces red. Cull the front faces to look inside the cube.",
    camera: { eye: [1.8, 1.4, 2.6], target: [0, 0, 0] },
    controls: [
      { id: "cull", type: "select", label: "setCullMode", value: "back", options: [["none", ".none"], ["back", ".back"], ["front", ".front"]] },
      { id: "front", type: "select", label: "setFrontFacing", value: "ccw", options: [["ccw", ".counterClockwise"], ["cw", ".clockwise"]] },
    ],
    state: (s) => ({ cull: s.cull, frontFace: s.front }),
    objects: (s, t) => [{ mesh: "cube", model: M.rotate(t * 0.4, 0, 1, 0) }],
    prelude: LIT,
    code: `
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              bool isFrontFace [[front_facing]]) {
    float3 normal = normalize(in.normal);
    float3 color = float3(0.2, 0.8, 0.35);
    if (!isFrontFace) {
        normal = -normal;
        color = float3(0.9, 0.25, 0.2);
    }
    float light = 0.35 + 0.65 * max(dot(normal, normalize(float3(0.4, 1.0, 0.6))), 0.0);
    return float4(color * light, 1.0);
}`,
  });

  LM.define("render-targets", {
    caption: "The scene is rendered into a texture; this fragment function then runs once per screen pixel.",
    camera: { eye: [0, 0, 3.6], target: [0, 0, -1.5] }, clear: () => [0.2, 0.3, 0.3],
    textures: { colorTexture: "crate" },
    controls: [{ id: "effect", type: "select", label: "effect", value: "3",
      options: [["0", "None"], ["1", "Inverted"], ["2", "Grayscale"], ["3", "Edge kernel"], ["4", "Blur kernel"]] }],
    uniforms: (s) => ({ effect: +s.effect }),
    objects: (s, t) => tenCubes(t),
    sceneSource: LIT + `
fragment float4 fragment_scene(VertexOut in [[stage_in]],
                               texture2d<float> colorTexture [[texture(0)]],
                               sampler s [[sampler(0)]]) {
    float light = 0.35 + 0.65 * max(dot(normalize(in.normal), normalize(float3(0.4, 1.0, 0.6))), 0.0);
    return float4(colorTexture.sample(s, in.uv).rgb * light, 1.0);
}`,
    prelude: SCREEN,
    code: `
struct PostUniforms {
    int effect;
};

constexpr sampler kernelSampler(filter::linear, address::clamp_to_edge);

static float3 applyKernel(texture2d<float> tex, float2 uv, const float kernel[9]) {
    float2 texel = 1.0 / float2(tex.get_width(), tex.get_height());
    float3 result = float3(0.0);
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            float3 c = tex.sample(kernelSampler, uv + float2(float(x), float(y)) * texel).rgb;
            result += c * kernel[(y + 1) * 3 + (x + 1)];
        }
    }
    return result;
}

fragment float4 fragment_post(ScreenOut in [[stage_in]],
                              constant PostUniforms &uniforms [[buffer(0)]],
                              texture2d<float> scene [[texture(0)]],
                              sampler s [[sampler(0)]]) {
    float3 color = scene.sample(s, in.uv).rgb;

    if (uniforms.effect == 1) {
        color = 1.0 - color;
    } else if (uniforms.effect == 2) {
        color = float3(dot(color, float3(0.2126, 0.7152, 0.0722)));
    } else if (uniforms.effect == 3) {
        const float edges[9] = { 1.0, 1.0, 1.0,   1.0, -8.0, 1.0,   1.0, 1.0, 1.0 };
        color = saturate(applyKernel(scene, in.uv, edges));
    } else if (uniforms.effect == 4) {
        const float blur[9] = { 0.0625, 0.125, 0.0625,   0.125, 0.25, 0.125,   0.0625, 0.125, 0.0625 };
        color = applyKernel(scene, in.uv, blur);
    }
    return float4(color, 1.0);
}`,
  });

  const SKY_BACKGROUND = SCREEN + SKY + `
struct Camera { float3 cameraFront; float3 cameraRight; float3 cameraUp; float tanHalfFov; float aspect; };
fragment float4 fragment_sky(ScreenOut in [[stage_in]], constant Camera &camera [[buffer(0)]]) {
    float2 ndc = float2(in.uv.x * 2.0 - 1.0, 1.0 - in.uv.y * 2.0);
    float3 d = normalize(camera.cameraFront + ndc.x * camera.aspect * camera.tanHalfFov * camera.cameraRight
                         + ndc.y * camera.tanHalfFov * camera.cameraUp);
    return float4(sky(d), 1.0);
}`;

  LM.define("cubemaps", {
    caption: "Drag to orbit. Slide from mirror to glass, and change the refractive index.",
    camera: { eye: [0, 0.5, 3.4], target: [0, 0, 0], fov: 50 }, animate: false,
    controls: [
      { id: "refract", label: "reflect to refract", min: 0, max: 1, value: 0 },
      { id: "ior", label: "refractive index", min: 1, max: 2.42, value: 1.52 },
      { id: "shape", type: "select", label: "shape", value: "sphere", options: [["sphere", "Sphere"], ["cube", "Cube"]] },
    ],
    uniforms: (s) => ({ refraction: s.refract, ior: s.ior }),
    objects: (s) => [{ mesh: s.shape, model: M.scale(s.shape === "cube" ? 1.3 : 2) }],
    backgroundSource: SKY_BACKGROUND,
    prelude: LIT + SKY,
    code: `
struct FragmentUniforms {
    float3 viewPosition;
    float refraction;
    float ior;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]]) {
    float3 incident = normalize(in.worldPosition - uniforms.viewPosition);
    float3 normal = normalize(in.normal);

    float3 reflected = sky(reflect(incident, normal));
    float3 refracted = sky(refract(incident, normal, 1.0 / uniforms.ior));

    return float4(mix(reflected, refracted, uniforms.refraction), 1.0);
}`,
  });

  LM.define("instancing", {
    caption: "One draw call. Every cube derives its place in the ring from its instance ID.",
    camera: { eye: [0, 9, 26], target: [0, -1, 0] }, clear: () => [0.01, 0.01, 0.03],
    controls: [{ id: "count", label: "instanceCount", min: 1, max: 20000, step: 1, value: 6000 }],
    uniforms: (s) => ({ count: s.count }),
    state: () => ({ cull: "back" }),
    objects: (s) => [{ mesh: "cube", model: M.ident(), instances: Math.round(s.count) }],
    code: `
struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
};

struct VertexOut {
    float4 position [[position]];
    float3 normal;
    float3 color;
};

struct Uniforms {
    float4x4 view;
    float4x4 projection;
    float time;
    float count;
};

// A cheap random number from the instance ID.
static float hash(float n) {
    return fract(sin(n * 12.9898) * 43758.5453);
}

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             uint instanceID [[instance_id]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    float id = float(instanceID);
    float angle = id / uniforms.count * 6.2831853 + uniforms.time * 0.05;
    float radius = 14.0 + hash(id) * 6.0;
    float3 center = float3(sin(angle) * radius, (hash(id + 0.5) - 0.5) * 1.6, cos(angle) * radius);
    float size = 0.06 + hash(id + 0.25) * 0.22;

    // Spin each rock around the y axis.
    float spin = hash(id + 0.75) * 6.28 + uniforms.time * (hash(id + 0.1) - 0.5);
    float c = cos(spin), s = sin(spin);
    float3 p = float3(in.position.x * c + in.position.z * s, in.position.y, in.position.z * c - in.position.x * s);
    float3 n = float3(in.normal.x * c + in.normal.z * s, in.normal.y, in.normal.z * c - in.normal.x * s);

    VertexOut out;
    out.position = uniforms.projection * uniforms.view * float4(center + p * size, 1.0);
    out.normal = n;
    out.color = float3(0.35 + hash(id + 0.9) * 0.3) * float3(1.0, 0.95, 0.88);
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]]) {
    float light = 0.08 + 0.92 * max(dot(normalize(in.normal), normalize(float3(1.0, 0.6, 0.8))), 0.0);
    return float4(in.color * light, 1.0);
}`,
  });

  // ---------------------------------------------------------------- advanced lighting

  LM.define("blinn-phong", {
    caption: "A light just above a floor. With Phong and a low exponent the highlight is cut off behind the light.",
    camera: { eye: [0, 0.6, 5], target: [0, -0.5, 0], fov: 50 }, clear: () => [0.02, 0.02, 0.02], animate: false,
    textures: { floorTexture: "planks" },
    controls: [
      { id: "blinn", type: "check", label: "Blinn-Phong", value: false },
      { id: "shininess", label: "shininess", min: 1, max: 64, step: 1, value: 8 },
    ],
    uniforms: (s) => ({ lightPosition: [0, -0.25, -0.5], useBlinn: s.blinn ? 1 : 0, shininess: s.shininess }),
    objects: () => [{ mesh: "plane", model: M.mul(M.translate(0, -0.5, 0), M.scale(28, 1, 28)) }, lamp([0, -0.25, -0.5], null, 0.08)],
    prelude: LIT,
    code: `
struct FragmentUniforms {
    float3 lightPosition;
    float3 viewPosition;
    float shininess;
    int useBlinn;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> floorTexture [[texture(0)]],
                              sampler s [[sampler(0)]]) {
    float3 albedo = floorTexture.sample(s, in.uv * 8.0).rgb;
    float3 normal = normalize(in.normal);
    float3 toLight = uniforms.lightPosition - in.worldPosition;
    float distance = length(toLight);
    float3 lightDir = toLight / distance;
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);

    float spec;
    if (uniforms.useBlinn != 0) {
        float3 halfwayDir = normalize(lightDir + viewDir);
        spec = pow(max(dot(normal, halfwayDir), 0.0), uniforms.shininess);
    } else {
        float3 reflectDir = reflect(-lightDir, normal);
        spec = pow(max(dot(viewDir, reflectDir), 0.0), uniforms.shininess);
    }

    float attenuation = 1.0 / (1.0 + 0.09 * distance + 0.032 * distance * distance);
    float diff = max(dot(normal, lightDir), 0.0);
    return float4(0.05 * albedo + (diff * albedo + spec) * attenuation, 1.0);
}`,
  });

  const SHADOW_OBJECTS = (t) => [floor(-0.5, 24, { colorTexture: "floorTexture" }),
    { mesh: "cube", model: M.chain(M.translate(0, 1.5, 0), M.rotate(t * 0.6, 0.3, 1, 0.2), M.scale(0.5)) },
    { mesh: "cube", model: M.translate(2, 0, 1) },
    { mesh: "cube", model: M.chain(M.translate(-1.2, 0.2, 1.8), M.rotate(rad(60), 1, 0, 1), M.scale(0.6)) }];

  LM.define("shadow-mapping", {
    caption: "Set the bias to zero to see shadow acne, raise it to see peter panning, and turn the filter off for hard edges.",
    camera: { eye: [1.5, 3.4, 7], target: [0.3, 0, 0.6] }, clear: () => [0.02, 0.02, 0.03],
    textures: { colorTexture: "crate", floorTexture: "planks" },
    controls: [
      { id: "bias", label: "depth bias", min: 0, max: 6, step: 0.1, value: 1.5 },
      { id: "angle", label: "light angle", min: -3.1, max: 3.1, value: 1.0 },
      { id: "pcf", type: "check", label: "3 x 3 filter", value: true },
    ],
    shadow: (s) => ({ eye: [Math.cos(s.angle) * 4, 6, Math.sin(s.angle) * 4], center: [0.3, 0, 0.6], size: 7, near: 1, far: 16, bias: s.bias }),
    uniforms: (s) => {
      const eye = [Math.cos(s.angle) * 4, 6, Math.sin(s.angle) * 4];
      return { lightDirection: LM.vec.norm(LM.vec.sub([0.3, 0, 0.6], eye)), filter3x3: s.pcf ? 1 : 0 };
    },
    objects: (s, t) => SHADOW_OBJECTS(t),
    prelude: `
struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
    float2 uv       [[attribute(2)]];
};

struct Uniforms {
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float3x3 normalMatrix;
    float4x4 lightViewProjection;
};

struct VertexOut {
    float4 position [[position]];
    float3 worldPosition;
    float3 normal;
    float2 uv;
    float4 shadowPosition;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    float4 world = uniforms.model * float4(in.position, 1.0);
    out.position = uniforms.projection * uniforms.view * world;
    out.worldPosition = world.xyz;
    out.normal = uniforms.normalMatrix * in.normal;
    out.uv = in.uv;
    out.shadowPosition = uniforms.lightViewProjection * world;   // position in the light's clip space
    return out;
}`,
    code: `
struct FragmentUniforms {
    float3 lightDirection;
    float3 viewPosition;
    int filter3x3;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> colorTexture [[texture(0)]],
                              depth2d<float> shadowMap [[texture(1)]],
                              sampler textureSampler [[sampler(0)]],
                              sampler shadowSampler [[sampler(1)]]) {
    // Light clip space -> shadow map coordinates. NDC y is up, texture v is down.
    float3 proj = in.shadowPosition.xyz / in.shadowPosition.w;
    float2 uv = proj.xy * float2(0.5, -0.5) + 0.5;

    float lit = 0.0;
    if (uniforms.filter3x3 != 0) {
        float2 texel = 1.0 / float2(shadowMap.get_width(), shadowMap.get_height());
        for (int x = -1; x <= 1; x++) {
            for (int y = -1; y <= 1; y++) {
                lit += shadowMap.sample_compare(shadowSampler, uv + float2(float(x), float(y)) * texel, proj.z);
            }
        }
        lit /= 9.0;
    } else {
        lit = shadowMap.sample_compare(shadowSampler, uv, proj.z);
    }
    if (proj.z > 1.0 || uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        lit = 1.0;      // outside the light's box
    }

    float3 albedo = colorTexture.sample(textureSampler, in.uv).rgb;
    float3 normal = normalize(in.normal);
    float3 lightDir = normalize(-uniforms.lightDirection);
    float3 halfwayDir = normalize(lightDir + normalize(uniforms.viewPosition - in.worldPosition));

    float3 ambient = 0.18 * albedo;
    float3 diffuse = max(dot(normal, lightDir), 0.0) * albedo;
    float3 specular = pow(max(dot(normal, halfwayDir), 0.0), 64.0) * float3(0.25);

    return float4(ambient + lit * (diffuse + specular), 1.0);
}`,
  });

  const TANGENT_PRELUDE = `
struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
    float2 uv       [[attribute(2)]];
    float3 tangent  [[attribute(4)]];
};

struct Uniforms {
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float3x3 normalMatrix;
};

struct VertexOut {
    float4 position [[position]];
    float3 worldPosition;
    float3 normal;
    float3 tangent;
    float2 uv;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    float4 world = uniforms.model * float4(in.position, 1.0);
    out.position = uniforms.projection * uniforms.view * world;
    out.worldPosition = world.xyz;
    out.normal = uniforms.normalMatrix * in.normal;
    out.tangent = uniforms.normalMatrix * in.tangent;
    out.uv = in.uv * 1.5;
    return out;
}`;
  const wall = () => [{ mesh: "plane", model: M.chain(M.rotate(rad(90), 1, 0, 0), M.scale(3.6, 1, 3.6)) }];

  LM.define("normal-mapping", {
    caption: "A single flat quad. Drag to change the angle and watch the light catch the edges of the bricks.",
    camera: { eye: [0.9, -0.3, 3.4], target: [0, 0, 0], fov: 50 }, clear: () => [0.02, 0.02, 0.02],
    textures: { albedoMap: "bricks", normalMap: "bricksNormal" },
    controls: [
      { id: "on", type: "check", label: "use the normal map", value: true },
      { id: "strength", label: "bump strength", min: 0, max: 3, value: 1 },
    ],
    uniforms: (s, t) => ({ lightPosition: [Math.cos(t * 0.7) * 1.3, Math.sin(t * 0.7) * 1.3, 0.8], useNormalMap: s.on ? 1 : 0, strength: s.strength }),
    objects: (s, t) => wall().concat([lamp([Math.cos(t * 0.7) * 1.3, Math.sin(t * 0.7) * 1.3, 0.8], null, 0.07)]),
    prelude: TANGENT_PRELUDE,
    code: `
struct FragmentUniforms {
    float3 lightPosition;
    float3 viewPosition;
    float strength;
    int useNormalMap;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> albedoMap [[texture(0)]],
                              texture2d<float> normalMap [[texture(1)]],
                              sampler s [[sampler(0)]]) {
    float3 N = normalize(in.normal);

    if (uniforms.useNormalMap != 0) {
        float3 T = normalize(in.tangent);
        T = normalize(T - dot(T, N) * N);          // make T perpendicular to N again
        float3 B = cross(N, T);

        float3 tangentNormal = normalMap.sample(s, in.uv).xyz * 2.0 - 1.0;
        tangentNormal.xy *= uniforms.strength;
        float3x3 TBN = float3x3(T, B, N);
        N = normalize(TBN * tangentNormal);
    }

    float3 albedo = albedoMap.sample(s, in.uv).rgb;
    float3 toLight = uniforms.lightPosition - in.worldPosition;
    float3 lightDir = normalize(toLight);
    float3 halfwayDir = normalize(lightDir + normalize(uniforms.viewPosition - in.worldPosition));
    float attenuation = 1.6 / (1.0 + dot(toLight, toLight));

    float diff = max(dot(N, lightDir), 0.0);
    float spec = pow(max(dot(N, halfwayDir), 0.0), 24.0) * 0.25;
    return float4(0.06 * albedo + (diff * albedo + spec) * attenuation, 1.0);
}`,
  });

  LM.define("parallax-mapping", {
    caption: "Drag to a shallow angle. With enough layers the bricks hide the mortar behind them.",
    camera: { eye: [2.4, -0.5, 1.7], target: [0.2, 0, 0], fov: 45 }, clear: () => [0.02, 0.02, 0.02], animate: false,
    textures: { albedoMap: "bricks", normalMap: "bricksNormal", depthMap: "bricksDepth" },
    controls: [
      { id: "scale", label: "height scale", min: 0, max: 0.15, step: 0.005, value: 0.07 },
      { id: "layers", label: "layers", min: 2, max: 64, step: 1, value: 32 },
    ],
    uniforms: (s) => ({ lightPosition: [1.2, 1.0, 1.2], heightScale: s.scale, layerCount: s.layers }),
    objects: wall,
    prelude: TANGENT_PRELUDE,
    code: `
struct FragmentUniforms {
    float3 lightPosition;
    float3 viewPosition;
    float heightScale;
    float layerCount;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> albedoMap [[texture(0)]],
                              texture2d<float> normalMap [[texture(1)]],
                              texture2d<float> depthMap  [[texture(2)]],
                              sampler s [[sampler(0)]]) {
    float3 N = normalize(in.normal);
    float3 T = normalize(in.tangent);
    float3 B = cross(N, T);
    float3x3 TBN = float3x3(T, B, N);

    // The view direction in tangent space. The bitangent points up, texture v points down.
    float3 viewDir = normalize(transpose(TBN) * (uniforms.viewPosition - in.worldPosition));
    float2 deltaUV = float2(-viewDir.x, viewDir.y) / max(viewDir.z, 0.05)
                   * uniforms.heightScale / uniforms.layerCount;
    float layerDepth = 1.0 / uniforms.layerCount;

    // Steep parallax: march until the ray is below the surface.
    float2 uv = in.uv;
    float currentLayer = 0.0;
    float mapDepth = depthMap.sample(s, uv, level(0.0)).r;
    for (int i = 0; i < 64; i++) {
        if (currentLayer >= mapDepth) { break; }
        uv += deltaUV;
        mapDepth = depthMap.sample(s, uv, level(0.0)).r;
        currentLayer += layerDepth;
    }

    // Parallax occlusion: interpolate between the last two steps.
    float2 previousUV = uv - deltaUV;
    float after = mapDepth - currentLayer;
    float before = depthMap.sample(s, previousUV, level(0.0)).r - currentLayer + layerDepth;
    uv = mix(uv, previousUV, saturate(after / min(after - before, -0.00001)));

    float3 tangentNormal = normalMap.sample(s, uv).xyz * 2.0 - 1.0;
    N = normalize(TBN * tangentNormal);

    float3 albedo = albedoMap.sample(s, uv).rgb;
    float3 toLight = uniforms.lightPosition - in.worldPosition;
    float3 lightDir = normalize(toLight);
    float attenuation = 2.4 / (1.0 + dot(toLight, toLight));
    return float4(0.06 * albedo + max(dot(N, lightDir), 0.0) * albedo * attenuation, 1.0);
}`,
  });

  LM.define("hdr", {
    caption: "The lights are far brighter than 1.0. Compare clamping with the tone mappers and change the exposure.",
    camera: { eye: [0.3, 1.6, 5.2], target: [0.2, 0.1, -0.5], fov: 50 }, clear: () => [0, 0, 0], animate: false,
    textures: { colorTexture: "crate", floorTexture: "planks" },
    controls: [
      { id: "op", type: "select", label: "tone mapping", value: "0", options: [["0", "None (clamped)"], ["1", "Reinhard"], ["2", "Exposure"], ["3", "ACES"]] },
      { id: "exposure", label: "exposure", min: 0.1, max: 5, value: 1 },
    ],
    uniforms: (s) => {
      const u = { op: +s.op, exposure: s.exposure };
      [[[-2.4, 0.3, 0.2], [14, 3.4, 2]], [[2.6, 0.5, -0.6], [3, 7, 14]], [[0.4, 0.2, 1.4], [4, 14, 6]], [[0.2, 1.8, -2.2], [14, 11, 4]]]
        .forEach((l, i) => { u["lights[" + i + "].position"] = l[0]; u["lights[" + i + "].color"] = l[1]; });
      return u;
    },
    objects: () => [floor(-0.5, 24, { colorTexture: "floorTexture" }),
      { mesh: "cube", model: M.mul(M.translate(-1.0, 0, -1.2), M.rotate(rad(25), 0, 1, 0)) },
      { mesh: "cube", model: M.mul(M.translate(1.4, 0, -0.2), M.rotate(rad(-15), 0, 1, 0)) },
      { mesh: "cube", model: M.chain(M.translate(0.2, 0.8, -1.0), M.rotate(rad(40), 0, 1, 0), M.scale(0.6)) },
      lamp([-2.4, 0.3, 0.2], [1, 0.5, 0.3]), lamp([2.6, 0.5, -0.6], [0.4, 0.6, 1]), lamp([0.4, 0.2, 1.4], [0.4, 1, 0.5]), lamp([0.2, 1.8, -2.2], [1, 0.85, 0.4])],
    prelude: LIT,
    code: `
struct PointLight {
    float3 position;
    float3 color;        // far above 1.0
};

struct FragmentUniforms {
    float3 viewPosition;
    float exposure;
    int op;
};

static float3 acesFilm(float3 x) {
    return saturate((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14));
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              constant PointLight *lights [[buffer(2)]],
                              texture2d<float> colorTexture [[texture(0)]],
                              sampler s [[sampler(0)]]) {
    // Decode the sRGB texture to linear by hand; the page has no sRGB render target.
    float3 albedo = pow(colorTexture.sample(s, in.uv).rgb, float3(2.2));
    float3 normal = normalize(in.normal);

    float3 hdr = 0.02 * albedo;
    for (int i = 0; i < 4; i++) {
        float3 toLight = lights[i].position - in.worldPosition;
        float distance = length(toLight);
        float diff = max(dot(normal, toLight / distance), 0.0);
        hdr += diff * albedo * lights[i].color / (distance * distance);
    }

    float3 mapped = hdr;                                              // 0: let the target clamp it
    if (uniforms.op == 1) { mapped = hdr / (hdr + 1.0); }             // Reinhard
    if (uniforms.op == 2) { mapped = 1.0 - exp(-hdr * uniforms.exposure); }
    if (uniforms.op == 3) { mapped = acesFilm(hdr * uniforms.exposure); }

    return float4(pow(mapped, float3(1.0 / 2.2)), 1.0);              // gamma encode
}`,
  });

  // ---------------------------------------------------------------- PBR

  LM.define("pbr", {
    caption: "A Cook-Torrance material lit by a point light and a procedural sky. Drag to orbit.",
    camera: { eye: [0, 0.3, 2.6], target: [0, 0, 0], fov: 40 },
    controls: [
      { id: "metallic", label: "metallic", min: 0, max: 1, value: 1 },
      { id: "roughness", label: "roughness", min: 0.05, max: 1, value: 0.3 },
      { id: "albedo", type: "color", label: "albedo", value: "#ff8b3c" },
    ],
    uniforms: (s, t) => ({ albedo: s.albedo.map((c) => Math.pow(c, 2.2)), metallic: s.metallic, roughness: s.roughness,
      lightPosition: [Math.cos(t * 0.5) * 4, 3, Math.sin(t * 0.5) * 4] }),
    objects: () => [{ mesh: "sphere", model: M.scale(1.7) }],
    backgroundSource: SKY_BACKGROUND,
    prelude: LIT + SKY,
    code: `
constant float PI = 3.14159265359;

struct Material {
    float3 viewPosition;
    float3 lightPosition;
    float3 albedo;
    float metallic;
    float roughness;
};

// D: how many microfacets line up with the halfway vector.
static float distributionGGX(float NdotH, float roughness) {
    float a2 = pow(roughness, 4.0);
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}

// G: microfacets shadowing each other.
static float geometrySchlickGGX(float NdotX, float roughness) {
    float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
    return NdotX / (NdotX * (1.0 - k) + k);
}

// F: more reflection at grazing angles.
static float3 fresnelSchlick(float cosTheta, float3 F0) {
    return F0 + (1.0 - F0) * pow(saturate(1.0 - cosTheta), 5.0);
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant Material &material [[buffer(1)]]) {
    float3 N = normalize(in.normal);
    float3 V = normalize(material.viewPosition - in.worldPosition);
    float3 F0 = mix(float3(0.04), material.albedo, material.metallic);
    float NdotV = max(dot(N, V), 0.0001);

    // One point light.
    float3 toLight = material.lightPosition - in.worldPosition;
    float3 L = normalize(toLight);
    float3 H = normalize(V + L);
    float NdotL = max(dot(N, L), 0.0);
    float3 radiance = float3(40.0) / dot(toLight, toLight);

    float D = distributionGGX(max(dot(N, H), 0.0), material.roughness);
    float G = geometrySchlickGGX(NdotV, material.roughness) * geometrySchlickGGX(NdotL, material.roughness);
    float3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

    float3 specular = D * G * F / (4.0 * NdotV * NdotL + 0.0001);
    float3 kD = (1.0 - F) * (1.0 - material.metallic);
    float3 color = (kD * material.albedo / PI + specular) * radiance * NdotL;

    // A rough stand-in for image-based lighting: the sky along the normal and the reflection.
    float3 Fa = fresnelSchlick(NdotV, F0);
    float3 reflection = mix(sky(reflect(-V, N)), sky(N) * 0.6 + 0.2, material.roughness);
    color += (1.0 - Fa) * (1.0 - material.metallic) * material.albedo * (sky(N) * 0.5 + 0.15);
    color += Fa * reflection * (1.0 - material.roughness * 0.6);

    color = color / (color + 1.0);                       // Reinhard
    return float4(pow(color, float3(1.0 / 2.2)), 1.0);    // gamma
}`,
  });

  // ---------------------------------------------------------------- in practice, beyond

  LM.define("debugging", {
    caption: "Debugging by color: write an intermediate value out as the fragment color.",
    camera: { eye: [0, 1.4, 4.4], target: [-0.3, 0, 0] }, clear: () => [0.12, 0.13, 0.16], animate: false,
    textures: { colorTexture: "crate" },
    controls: [{ id: "view", type: "select", label: "show", value: "1",
      options: [["0", "Final color"], ["1", "Normals"], ["2", "Texture coordinates"], ["3", "Linear depth"], ["4", "World position (fract)"]] }],
    uniforms: (s) => ({ mode: +s.view }),
    objects: () => [{ mesh: "sphere", model: M.mul(M.translate(-1.5, 0, 0), M.scale(1.5)) },
      { mesh: "cube", model: M.chain(M.translate(0.5, 0, 0), M.rotate(rad(35), 0.2, 1, 0.1), M.scale(1.1)) }, floor(-0.75, 8)],
    prelude: LIT,
    code: `
struct FragmentUniforms {
    int mode;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> colorTexture [[texture(0)]],
                              sampler s [[sampler(0)]]) {
    float3 normal = normalize(in.normal);

    if (uniforms.mode == 1) { return float4(normal * 0.5 + 0.5, 1.0); }
    if (uniforms.mode == 2) { return float4(fract(in.uv), 0.0, 1.0); }
    if (uniforms.mode == 3) {
        float z = 0.1 * 100.0 / (100.0 - in.position.z * (100.0 - 0.1));
        return float4(float3(z / 9.0), 1.0);
    }
    if (uniforms.mode == 4) { return float4(fract(in.worldPosition), 1.0); }

    float light = 0.25 + 0.75 * max(dot(normal, normalize(float3(0.5, 1.0, 0.7))), 0.0);
    return float4(colorTexture.sample(s, in.uv).rgb * light, 1.0);
}`,
  });

  LM.define("ray-tracing", {
    caption: "A ray tracer in a fragment function: no triangles, one primary ray per pixel, then shadow and reflection rays.",
    animate: true, fullscreen: true, camera: { eye: [0, 1.6, 5.5], target: [0, 0.6, 0], fov: 45 },
    controls: [{ id: "bounces", label: "reflection bounces", min: 0, max: 3, step: 1, value: 1 }],
    uniforms: (s, t) => ({ bounces: s.bounces, lightPosition: [Math.cos(t * 0.6) * 4, 5, Math.sin(t * 0.6) * 4] }),
    objects: () => [],
    prelude: SCREEN,
    code: `
struct Camera {
    float3 viewPosition;
    float3 cameraFront;
    float3 cameraRight;
    float3 cameraUp;
    float3 lightPosition;
    float tanHalfFov;
    float aspect;
    float bounces;
};

struct Hit {
    float distance;
    float3 normal;
    float3 color;
    float mirror;
};

static void sphere(float3 origin, float3 direction, float3 center, float radius, float3 color, float mirror, Hit &hit) {
    float3 oc = origin - center;
    float b = dot(oc, direction);
    float disc = b * b - (dot(oc, oc) - radius * radius);
    if (disc < 0.0) { return; }
    float t = -b - sqrt(disc);
    if (t > 0.001 && t < hit.distance) {
        hit.distance = t;
        hit.normal = (origin + direction * t - center) / radius;
        hit.color = color;
        hit.mirror = mirror;
    }
}

// What does this ray hit first? In Metal this is intersector.intersect(ray, accelerationStructure).
static Hit intersect(float3 origin, float3 direction) {
    Hit hit;
    hit.distance = 1000.0;
    hit.mirror = 0.0;
    sphere(origin, direction, float3(-1.3, 0.6, 0.0), 0.6, float3(0.9, 0.3, 0.2), 0.1, hit);
    sphere(origin, direction, float3(0.0, 0.8, -0.6), 0.8, float3(0.9, 0.9, 0.9), 0.85, hit);
    sphere(origin, direction, float3(1.4, 0.5, 0.4), 0.5, float3(0.2, 0.45, 0.9), 0.25, hit);

    float t = -origin.y / direction.y;                    // the ground plane y = 0
    if (direction.y < 0.0 && t > 0.001 && t < hit.distance) {
        float3 p = origin + direction * t;
        float checker = abs(fmod(floor(p.x) + floor(p.z), 2.0));
        hit.distance = t;
        hit.normal = float3(0.0, 1.0, 0.0);
        hit.color = mix(float3(0.75), float3(0.35), checker);
        hit.mirror = 0.15;
    }
    return hit;
}

fragment float4 fragment_main(ScreenOut in [[stage_in]],
                              constant Camera &camera [[buffer(0)]]) {
    float2 ndc = float2(in.uv.x * 2.0 - 1.0, 1.0 - in.uv.y * 2.0);
    float3 origin = camera.viewPosition;
    float3 direction = normalize(camera.cameraFront
                               + ndc.x * camera.aspect * camera.tanHalfFov * camera.cameraRight
                               + ndc.y * camera.tanHalfFov * camera.cameraUp);

    float3 color = float3(0.0);
    float3 weight = float3(1.0);
    for (int bounce = 0; bounce < 4; bounce++) {
        Hit hit = intersect(origin, direction);
        if (hit.distance > 999.0) {
            color += weight * mix(float3(0.8, 0.87, 1.0), float3(0.25, 0.45, 0.85), saturate(direction.y));
            break;
        }
        float3 p = origin + direction * hit.distance;

        // Shadow ray: is anything between this point and the light?
        float3 toLight = camera.lightPosition - p;
        float lightDistance = length(toLight);
        float3 lightDir = toLight / lightDistance;
        Hit blocker = intersect(p + hit.normal * 0.002, lightDir);
        float lit = blocker.distance < lightDistance ? 0.0 : 1.0;

        float3 shaded = hit.color * (0.15 + lit * max(dot(hit.normal, lightDir), 0.0));
        color += weight * shaded * (1.0 - hit.mirror);

        // Reflection ray.
        if (float(bounce) >= camera.bounces) { break; }
        weight *= hit.mirror;
        origin = p + hit.normal * 0.002;
        direction = reflect(direction, hit.normal);
    }
    return float4(pow(color, float3(1.0 / 2.2)), 1.0);
}`,
  });

  // ---------------------------------------------------------------- 2D canvas demos

  LM.define("tessellation", {
    caption: "A 4 x 4 grid of quad patches. The tessellation factor decides how finely each one is subdivided.",
    controls: [
      { id: "factor", label: "tessellation factor", min: 1, max: 16, step: 1, value: 4 },
      { id: "height", label: "height scale", min: 0, max: 2, value: 1 },
    ],
    custom(canvas, state) {
      const ctx = canvas.getContext("2d");
      const height = (x, z) => Math.sin(x * 1.3) * Math.cos(z * 1.1) * 0.5 + Math.sin(x * 2.9 + 1) * Math.sin(z * 2.3) * 0.22 + Math.cos(x * 0.6 - z * 0.8) * 0.45;
      let angle = 0.5, drag = null;
      function redraw() {
        const dpr = Math.min(devicePixelRatio || 1, 2), w = canvas.clientWidth * dpr, h = canvas.clientHeight * dpr;
        if (canvas.width !== w) { canvas.width = w; canvas.height = h; }
        ctx.fillStyle = "#12161c"; ctx.fillRect(0, 0, w, h);
        const n = 4 * state.factor, eye = [Math.sin(angle) * 7, 3.6, Math.cos(angle) * 7];
        const view = M.lookAt(eye, [0, -0.2, 0], [0, 1, 0]), proj = M.perspective(rad(42), w / h, 0.1, 100), vp = M.mul(proj, view);
        const pts = [];
        for (let i = 0; i <= n; i++) for (let j = 0; j <= n; j++) {
          const x = -3 + (6 * j) / n, z = -3 + (6 * i) / n, y = height(x, z) * state.height;
          const cw = vp[3] * x + vp[7] * y + vp[11] * z + vp[15];
          pts.push([((vp[0] * x + vp[4] * y + vp[8] * z + vp[12]) / cw * 0.5 + 0.5) * w,
            (0.5 - (vp[1] * x + vp[5] * y + vp[9] * z + vp[13]) / cw * 0.5) * h, y]);
        }
        const P = (i, j) => pts[i * (n + 1) + j];
        ctx.lineWidth = dpr;
        for (let i = 0; i <= n; i++) for (let j = 0; j <= n; j++) {
          const a = P(i, j), patchEdge = i % state.factor === 0 || j % state.factor === 0;
          const k = Math.max(0, Math.min(1, (a[2] / (state.height || 1) + 0.9) / 1.9));
          ctx.strokeStyle = "rgb(" + Math.round(70 + 185 * k) + "," + Math.round(120 + 30 * k) + "," + Math.round(140 - 80 * k) + ")";
          ctx.globalAlpha = patchEdge ? 1 : 0.55;
          ctx.beginPath();
          if (j < n) { ctx.moveTo(a[0], a[1]); ctx.lineTo(P(i, j + 1)[0], P(i, j + 1)[1]); }
          if (i < n) { ctx.moveTo(a[0], a[1]); ctx.lineTo(P(i + 1, j)[0], P(i + 1, j)[1]); }
          if (i < n && j < n) { ctx.moveTo(a[0], a[1]); ctx.lineTo(P(i + 1, j + 1)[0], P(i + 1, j + 1)[1]); }
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
      canvas.classList.add("lm-grab");
      canvas.addEventListener("pointerdown", (e) => { drag = e.clientX; canvas.setPointerCapture(e.pointerId); });
      canvas.addEventListener("pointerup", () => { drag = null; });
      canvas.addEventListener("pointermove", (e) => { if (drag !== null) { angle -= (e.clientX - drag) * 0.008; drag = e.clientX; redraw(); } });
      new ResizeObserver(redraw).observe(canvas);
      return { redraw };
    },
  });

  LM.define("breakout", {
    caption: "Playable: move the paddle with the mouse, a finger, or the arrow keys. Click or press Space to launch.",
    aspect: 4 / 3, maxWidth: 640,
    custom(canvas) {
      const ctx = canvas.getContext("2d"), W = 800, H = 600;
      const palette = ["#e64d4d", "#e69933", "#4dcc66", "#4d80e6"];
      let bricks, paddle, ball, lives, score, keys = {}, last = 0, visible = false;
      function reset() {
        bricks = [];
        for (let r = 0; r < 6; r++) for (let c = 0; c < 12; c++) bricks.push({ x: c * (W / 12), y: 60 + r * 24, w: W / 12 - 2, h: 22, color: palette[r % 4], alive: true });
        paddle = { x: 350, y: 570, w: 100, h: 16 };
        ball = { x: 400, y: 560, vx: 150, vy: -360, r: 9, stuck: true };
        lives = 3; score = 0;
      }
      function collide(b, r) {
        const cx = Math.max(r.x, Math.min(b.x, r.x + r.w)), cy = Math.max(r.y, Math.min(b.y, r.y + r.h));
        const dx = b.x - cx, dy = b.y - cy;
        if (dx * dx + dy * dy >= b.r * b.r) return null;
        return Math.abs(dx) > Math.abs(dy) ? [Math.sign(dx), 0] : [0, Math.sign(dy) || -1];
      }
      function update(dt) {
        paddle.x += ((keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0)) * 520 * dt;
        paddle.x = Math.max(0, Math.min(W - paddle.w, paddle.x));
        if (ball.stuck) { ball.x = paddle.x + paddle.w / 2; ball.y = paddle.y - ball.r; return; }
        ball.x += ball.vx * dt; ball.y += ball.vy * dt;
        if (ball.x < ball.r || ball.x > W - ball.r) { ball.vx = -ball.vx; ball.x = Math.max(ball.r, Math.min(W - ball.r, ball.x)); }
        if (ball.y < ball.r) ball.vy = Math.abs(ball.vy);
        for (const b of bricks) {
          if (!b.alive) continue;
          const n = collide(ball, b);
          if (n) { b.alive = false; score += 10; if (n[0]) ball.vx = Math.abs(ball.vx) * n[0]; else ball.vy = Math.abs(ball.vy) * n[1]; break; }
        }
        if (ball.vy > 0 && collide(ball, paddle)) {
          const offset = (ball.x - (paddle.x + paddle.w / 2)) / (paddle.w / 2), speed = Math.hypot(ball.vx, ball.vy);
          const l = Math.hypot(offset, 1.2);
          ball.vx = (offset / l) * speed; ball.vy = (-1.2 / l) * speed;
        }
        if (ball.y > H + ball.r) { lives--; ball.stuck = true; ball.vx = 150; ball.vy = -360; if (lives <= 0) reset(); }
        if (bricks.every((b) => !b.alive)) reset();
      }
      function draw() {
        const dpr = Math.min(devicePixelRatio || 1, 2), w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
        if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
        ctx.setTransform(w / W, 0, 0, h / H, 0, 0);
        ctx.fillStyle = "#12161c"; ctx.fillRect(0, 0, W, H);
        for (const b of bricks) if (b.alive) { ctx.fillStyle = b.color; ctx.fillRect(b.x + 1, b.y + 1, b.w, b.h); }
        ctx.fillStyle = "#e8e8e8"; ctx.fillRect(paddle.x, paddle.y, paddle.w, paddle.h);
        ctx.beginPath(); ctx.arc(ball.x, ball.y, ball.r, 0, 7); ctx.fillStyle = "#fff"; ctx.fill();
        ctx.font = "20px ui-monospace, Menlo, monospace"; ctx.fillStyle = "#e8e8e8";
        ctx.fillText("SCORE " + score, 16, 34); ctx.fillText("LIVES " + lives, 690, 34);
        if (ball.stuck) { ctx.textAlign = "center"; ctx.fillText("Click or press Space to launch", W / 2, 380); ctx.textAlign = "left"; }
      }
      function loop(now) {
        if (!visible) return;
        const dt = Math.min((now - last) / 1000, 0.05); last = now;
        for (let i = 0; i < 4; i++) update(dt / 4);      // sub-steps keep a fast ball from tunneling
        draw();
        requestAnimationFrame(loop);
      }
      const pointer = (e) => { const r = canvas.getBoundingClientRect(); paddle.x = ((e.clientX - r.left) / r.width) * W - paddle.w / 2; };
      canvas.tabIndex = 0;
      canvas.style.touchAction = "none";
      canvas.addEventListener("pointermove", pointer);
      canvas.addEventListener("pointerdown", (e) => { pointer(e); ball.stuck = false; canvas.focus({ preventScroll: true }); });
      canvas.addEventListener("keydown", (e) => {
        if (e.key === " " || e.key.startsWith("Arrow")) e.preventDefault();
        if (e.key === " ") ball.stuck = false;
        keys[e.key] = true;
      });
      canvas.addEventListener("keyup", (e) => { keys[e.key] = false; });
      reset();
      new IntersectionObserver((en) => {
        const was = visible; visible = en[0].isIntersecting;
        if (visible && !was) { last = performance.now(); requestAnimationFrame(loop); }
      }).observe(canvas);
    },
  });
})();
