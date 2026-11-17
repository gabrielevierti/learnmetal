#include <metal_stdlib>
using namespace metal;

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
    float3 sunDirection;
    float3 sunColor;
    float3 spotPosition;
    float3 spotDirection;
    float2 spotCutoff;
    uint pointLightCount;
    uint spotEnabled;
};

struct Surface {
    float3 position;
    float3 normal;
    float3 viewDir;
    float3 albedo;
    float3 specular;
    float shininess;
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

// Diffuse + specular for one light direction, without ambient.
static float3 phong(Surface s, float3 lightDir, float3 lightColor) {
    float diff = max(dot(s.normal, lightDir), 0.0);
    float spec = pow(max(dot(s.viewDir, reflect(-lightDir, s.normal)), 0.0), s.shininess);
    return (diff * s.albedo + spec * s.specular) * lightColor;
}

static float attenuation(float distance) {
    return 1.0 / (1.0 + 0.09 * distance + 0.032 * distance * distance);
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
    s.shininess = 32.0;

    float3 color = 0.06 * s.albedo;

    // Directional light
    color += phong(s, normalize(-uniforms.sunDirection), uniforms.sunColor);

    // Point lights
    for (uint i = 0; i < uniforms.pointLightCount; i++) {
        float3 toLight = pointLights[i].position - s.position;
        float distance = length(toLight);
        color += phong(s, toLight / distance, pointLights[i].color) * attenuation(distance);
    }

    // Spotlight
    if (uniforms.spotEnabled != 0) {
        float3 toLight = uniforms.spotPosition - s.position;
        float distance = length(toLight);
        float3 lightDir = toLight / distance;
        float theta = dot(lightDir, normalize(-uniforms.spotDirection));
        float epsilon = uniforms.spotCutoff.x - uniforms.spotCutoff.y;
        float intensity = saturate((theta - uniforms.spotCutoff.y) / epsilon);
        color += phong(s, lightDir, float3(1.0)) * attenuation(distance) * intensity;
    }

    return float4(color, 1.0);
}

fragment float4 fragment_lamp(VertexOut in [[stage_in]],
                              constant float3 &color [[buffer(1)]]) {
    return float4(color, 1.0);
}
