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
    float4 shadowPosition;
};

struct Uniforms {
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float3x3 normalMatrix;
    float4x4 lightViewProjection;
};

struct FragmentUniforms {
    float3 lightDirection;
    float3 viewPosition;
};

// Pass 1: position in the light's clip space. A vertex function may return a bare float4.
vertex float4 vertex_shadow(VertexIn in [[stage_in]],
                            constant Uniforms &uniforms [[buffer(1)]]) {
    return uniforms.lightViewProjection * uniforms.model * float4(in.position, 1.0);
}

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    float4 world = uniforms.model * float4(in.position, 1.0);
    out.position = uniforms.projection * uniforms.view * world;
    out.worldPosition = world.xyz;
    out.normal = uniforms.normalMatrix * in.normal;
    out.uv = in.uv;
    out.shadowPosition = uniforms.lightViewProjection * world;
    return out;
}

// Returns 1 where the fragment is lit and 0 where it is in shadow, with 3x3 filtering.
static float calcShadow(float4 shadowPosition, depth2d<float> shadowMap, sampler shadowSampler) {
    float3 proj = shadowPosition.xyz / shadowPosition.w;
    // NDC has y up and runs from -1 to 1. Texture coordinates have y down and run from 0 to 1.
    float2 uv = proj.xy * float2(0.5, -0.5) + 0.5;

    if (proj.z > 1.0 || uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        return 1.0;     // outside the light's box
    }

    float2 texel = 1.0 / float2(shadowMap.get_width(), shadowMap.get_height());
    float lit = 0.0;
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            lit += shadowMap.sample_compare(shadowSampler, uv + float2(x, y) * texel, proj.z);
        }
    }
    return lit / 9.0;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant FragmentUniforms &uniforms [[buffer(1)]],
                              texture2d<float> colorTexture [[texture(0)]],
                              depth2d<float> shadowMap [[texture(1)]],
                              sampler textureSampler [[sampler(0)]],
                              sampler shadowSampler [[sampler(1)]]) {
    float3 albedo = colorTexture.sample(textureSampler, in.uv).rgb;
    float3 normal = normalize(in.normal);
    float3 lightDir = normalize(-uniforms.lightDirection);
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    float3 halfwayDir = normalize(lightDir + viewDir);

    float3 ambient = 0.12 * albedo;
    float3 diffuse = max(dot(normal, lightDir), 0.0) * albedo;
    float3 specular = pow(max(dot(normal, halfwayDir), 0.0), 64.0) * float3(0.25);

    float lit = calcShadow(in.shadowPosition, shadowMap, shadowSampler);
    return float4(ambient + lit * (diffuse + specular), 1.0);
}
