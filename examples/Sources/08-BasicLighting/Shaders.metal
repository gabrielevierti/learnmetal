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
                              constant FragmentUniforms &uniforms [[buffer(1)]]) {
    Material material = uniforms.material;
    Light light = uniforms.light;

    float3 normal = normalize(in.normal);
    float3 lightDir = normalize(light.position - in.worldPosition);
    float3 viewDir = normalize(uniforms.viewPosition - in.worldPosition);
    float3 reflectDir = reflect(-lightDir, normal);

    float3 ambient = light.ambient * material.ambient;

    float diff = max(dot(normal, lightDir), 0.0);
    float3 diffuse = light.diffuse * (diff * material.diffuse);

    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);
    float3 specular = light.specular * (spec * material.specular);

    return float4(ambient + diffuse + specular, 1.0);
}

fragment float4 fragment_lamp(VertexOut in [[stage_in]]) {
    return float4(1.0);
}
