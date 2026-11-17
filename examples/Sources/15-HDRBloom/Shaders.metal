#include <metal_stdlib>
using namespace metal;

// ---------------------------------------------------------------- scene (HDR, two outputs)

struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
    float2 uv       [[attribute(2)]];
};

struct VertexOut {
    float4 position [[position]];
    float3 worldPosition;
    float3 normal;
    float2 uv;
};

struct Uniforms {
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float3x3 normalMatrix;
};

struct PointLight {
    float3 position;
    float3 color;
};

struct FragmentUniforms {
    float3 viewPosition;
    uint lightCount;
};

struct SceneOut {
    float4 color  [[color(0)]];
    float4 bright [[color(1)]];
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
}

static SceneOut splitBright(float3 color) {
    SceneOut out;
    out.color = float4(color, 1.0);
    float brightness = dot(color, float3(0.2126, 0.7152, 0.0722));
    out.bright = brightness > 1.0 ? float4(color, 1.0) : float4(0.0, 0.0, 0.0, 1.0);
    return out;
}

fragment SceneOut fragment_main(VertexOut in [[stage_in]],
                                constant FragmentUniforms &uniforms [[buffer(1)]],
                                constant PointLight *lights [[buffer(2)]],
                                texture2d<float> colorTexture [[texture(0)]],
                                sampler textureSampler [[sampler(0)]]) {
    float3 albedo = colorTexture.sample(textureSampler, in.uv).rgb;
    float3 normal = normalize(in.normal);
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);

    float3 color = 0.02 * albedo;
    for (uint i = 0; i < uniforms.lightCount; i++) {
        float3 toLight = lights[i].position - in.worldPosition;
        float distance = length(toLight);
        float3 lightDir = toLight / distance;
        float3 halfwayDir = normalize(lightDir + viewDir);

        float diff = max(dot(normal, lightDir), 0.0);
        float spec = pow(max(dot(normal, halfwayDir), 0.0), 64.0) * 0.3;
        float attenuation = 1.0 / (distance * distance);        // inverse square: correct in linear space
        color += (diff * albedo + spec) * lights[i].color * attenuation;
    }
    return splitBright(color);
}

fragment SceneOut fragment_lamp(VertexOut in [[stage_in]],
                                constant float3 &color [[buffer(1)]]) {
    return splitBright(color);
}

// ---------------------------------------------------------------- full-screen passes

struct ScreenOut {
    float4 position [[position]];
    float2 uv;
};

vertex ScreenOut vertex_fullscreen(uint vertexID [[vertex_id]]) {
    float2 uv = float2((vertexID << 1) & 2, vertexID & 2);
    ScreenOut out;
    out.position = float4(uv * float2(2, -2) + float2(-1, 1), 0, 1);
    out.uv = uv;
    return out;
}

// One direction of a separable 9-tap Gaussian blur.
fragment float4 fragment_blur(ScreenOut in [[stage_in]],
                              constant float2 &direction [[buffer(0)]],
                              texture2d<float> image [[texture(0)]],
                              sampler s [[sampler(0)]]) {
    const float weights[5] = { 0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216 };
    float2 texel = direction / float2(image.get_width(), image.get_height());

    float3 result = image.sample(s, in.uv).rgb * weights[0];
    for (int i = 1; i < 5; i++) {
        result += image.sample(s, in.uv + texel * float(i)).rgb * weights[i];
        result += image.sample(s, in.uv - texel * float(i)).rgb * weights[i];
    }
    return float4(result, 1.0);
}

struct CompositeUniforms {
    float exposure;
    float bloomStrength;
};

fragment float4 fragment_composite(ScreenOut in [[stage_in]],
                                   constant CompositeUniforms &uniforms [[buffer(0)]],
                                   texture2d<float> scene [[texture(0)]],
                                   texture2d<float> bloom [[texture(1)]],
                                   sampler s [[sampler(0)]]) {
    float3 hdr = scene.sample(s, in.uv).rgb;
    hdr += bloom.sample(s, in.uv).rgb * uniforms.bloomStrength;     // add the glow before tone mapping

    float3 mapped = 1.0 - exp(-hdr * uniforms.exposure);             // exposure tone mapping
    return float4(mapped, 1.0);                                      // the sRGB drawable applies gamma
}
