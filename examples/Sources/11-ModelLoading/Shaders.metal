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
    float3 baseColor;
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
                              bool isFrontFace [[front_facing]],
                              texture2d<float> baseColorTexture [[texture(0)]],
                              sampler mapSampler [[sampler(0)]]) {
    float3 albedo = baseColorTexture.sample(mapSampler, in.uv).rgb * uniforms.baseColor;

    // Culling is off in this example, so light both sides of every triangle.
    float3 normal = normalize(in.normal);
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    if (dot(normal, viewDir) < 0.0) {
        normal = -normal;
    }

    float3 lightDir = normalize(uniforms.lightPosition - in.worldPosition);
    float3 halfwayDir = normalize(lightDir + viewDir);

    float3 ambient = 0.15 * albedo;
    float3 diffuse = max(dot(normal, lightDir), 0.0) * albedo;
    float3 specular = pow(max(dot(normal, halfwayDir), 0.0), 48.0) * float3(0.4);

    return float4(ambient + diffuse + specular, 1.0);
}
