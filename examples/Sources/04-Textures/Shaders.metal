#include <metal_stdlib>
using namespace metal;

struct VertexIn {
    float3 position [[attribute(0)]];
    float2 uv       [[attribute(1)]];
};

struct VertexOut {
    float4 position [[position]];
    float2 uv;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]]) {
    VertexOut out;
    out.position = float4(in.position, 1.0);
    out.uv = in.uv;
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              constant float &mixFactor [[buffer(0)]],
                              texture2d<float> texture0 [[texture(0)]],
                              texture2d<float> texture1 [[texture(1)]],
                              sampler textureSampler [[sampler(0)]]) {
    float4 a = texture0.sample(textureSampler, in.uv);
    float4 b = texture1.sample(textureSampler, in.uv);
    return mix(a, b, mixFactor);
}
