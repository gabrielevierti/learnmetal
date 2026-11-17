#include <metal_stdlib>
using namespace metal;

constant float PI = 3.14159265359;

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

struct PBRUniforms {
    float3 viewPosition;
    float3 albedo;
    float metallic;
    float roughness;
    float ao;
    uint lightCount;
};

struct PBRLight {
    float3 position;
    float3 color;
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

// D: how many microfacets are aligned with the halfway vector (Trowbridge-Reitz GGX).
static float distributionGGX(float3 N, float3 H, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}

// G: microfacets shadowing and masking each other (Schlick-GGX, combined with Smith's method).
static float geometrySchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}

static float geometrySmith(float3 N, float3 V, float3 L, float roughness) {
    return geometrySchlickGGX(max(dot(N, V), 0.0), roughness)
         * geometrySchlickGGX(max(dot(N, L), 0.0), roughness);
}

// F: surfaces reflect more at grazing angles (Fresnel-Schlick).
static float3 fresnelSchlick(float cosTheta, float3 F0) {
    return F0 + (1.0 - F0) * pow(saturate(1.0 - cosTheta), 5.0);
}

fragment float4 fragment_pbr(VertexOut in [[stage_in]],
                             constant PBRUniforms &uniforms [[buffer(1)]],
                             constant PBRLight *lights [[buffer(2)]]) {
    float3 N = normalize(in.normal);
    float3 V = normalize(uniforms.viewPosition - in.worldPosition);

    float3 albedo = uniforms.albedo;
    float metallic = uniforms.metallic;
    float roughness = uniforms.roughness;

    // Base reflectivity: 0.04 for dielectrics, the albedo color for metals.
    float3 F0 = mix(float3(0.04), albedo, metallic);

    float3 Lo = float3(0.0);
    for (uint i = 0; i < uniforms.lightCount; i++) {
        float3 toLight = lights[i].position - in.worldPosition;
        float distance = length(toLight);
        float3 L = toLight / distance;
        float3 H = normalize(V + L);
        float3 radiance = lights[i].color / (distance * distance);

        float D = distributionGGX(N, H, roughness);
        float G = geometrySmith(N, V, L, roughness);
        float3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

        float NdotL = max(dot(N, L), 0.0);
        float3 specular = (D * G * F) / (4.0 * max(dot(N, V), 0.0) * NdotL + 0.0001);

        // Energy conservation: what is reflected cannot also be diffused. Metals have no diffuse.
        float3 kD = (1.0 - F) * (1.0 - metallic);

        Lo += (kD * albedo / PI + specular) * radiance * NdotL;
    }

    float3 ambient = float3(0.03) * albedo * uniforms.ao;
    float3 color = ambient + Lo;

    color = color / (color + 1.0);      // Reinhard tone mapping; the sRGB drawable applies gamma
    return float4(color, 1.0);
}
