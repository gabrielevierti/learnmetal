#include <metal_stdlib>
using namespace metal;

struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
    float2 uv       [[attribute(2)]];
};

struct VertexOut {
    float4 position [[position]];
    float3 normal;
    float4 color;
};

struct FrameUniforms {
    float4x4 view;
    float4x4 projection;
    float time;
};

struct InstanceData {
    float4x4 model;
    float4 color;
};

vertex VertexOut vertex_instanced(VertexIn in [[stage_in]],
                                  uint instanceID [[instance_id]],
                                  constant FrameUniforms &frame [[buffer(1)]],
                                  const device InstanceData *instances [[buffer(2)]]) {
    InstanceData instance = instances[instanceID];

    // Rotate the whole ring around the y axis over time. No CPU work per instance.
    float angle = frame.time * 0.05;
    float c = cos(angle), s = sin(angle);
    float4x4 orbit = float4x4(float4(c, 0, -s, 0),
                              float4(0, 1,  0, 0),
                              float4(s, 0,  c, 0),
                              float4(0, 0,  0, 1));
    float4x4 model = orbit * instance.model;

    VertexOut out;
    out.position = frame.projection * frame.view * model * float4(in.position, 1.0);
    // Valid because the instance matrices only rotate and scale uniformly.
    out.normal = (model * float4(in.normal, 0.0)).xyz;
    out.color = instance.color;
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]]) {
    float3 lightDir = normalize(float3(1.0, 0.6, 0.8));
    float light = 0.08 + 0.92 * max(dot(normalize(in.normal), lightDir), 0.0);
    return float4(in.color.rgb * light, 1.0);
}
