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

struct FragmentUniforms {
    float3 lightPosition;
    float3 viewPosition;
    float shininess;
    uint useSpecularMap;
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
}

fragment float4 fragment_lamp(VertexOut in [[stage_in]]) {
    return float4(1.0);
}
