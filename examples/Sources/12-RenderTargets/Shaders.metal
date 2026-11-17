#include <metal_stdlib>
using namespace metal;

// ---------------------------------------------------------------- scene

struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
    float2 uv       [[attribute(2)]];
};

struct VertexOut {
    float4 position [[position]];
    float3 normal;
    float2 uv;
};

struct Uniforms {
    float4x4 model;
    float4x4 view;
    float4x4 projection;
    float3x3 normalMatrix;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    out.position = uniforms.projection * uniforms.view * uniforms.model * float4(in.position, 1.0);
    out.normal = uniforms.normalMatrix * in.normal;
    out.uv = in.uv;
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]],
                              texture2d<float> colorTexture [[texture(0)]],
                              sampler textureSampler [[sampler(0)]]) {
    float3 albedo = colorTexture.sample(textureSampler, in.uv).rgb;
    float light = 0.35 + 0.65 * max(dot(normalize(in.normal), normalize(float3(0.4, 1.0, 0.6))), 0.0);
    return float4(albedo * light, 1.0);
}

// ---------------------------------------------------------------- post-processing

struct ScreenOut {
    float4 position [[position]];
    float2 uv;
};

// One oversized triangle that covers the screen. No vertex buffer needed.
vertex ScreenOut vertex_fullscreen(uint vertexID [[vertex_id]]) {
    float2 uv = float2((vertexID << 1) & 2, vertexID & 2);   // (0,0) (2,0) (0,2)
    ScreenOut out;
    out.position = float4(uv * float2(2, -2) + float2(-1, 1), 0, 1);
    out.uv = uv;
    return out;
}

static float3 applyKernel(texture2d<float> tex, sampler s, float2 uv, const float kernel[9]) {
    float2 texel = 1.0 / float2(tex.get_width(), tex.get_height());
    float3 result = float3(0);
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            float3 c = tex.sample(s, uv + float2(x, y) * texel).rgb;
            result += c * kernel[(y + 1) * 3 + (x + 1)];
        }
    }
    return result;
}

fragment float4 fragment_post(ScreenOut in [[stage_in]],
                              constant uint &effect [[buffer(0)]],
                              texture2d<float> scene [[texture(0)]],
                              sampler s [[sampler(0)]]) {
    float3 color = scene.sample(s, in.uv).rgb;

    if (effect == 1) {
        color = 1.0 - color;
    } else if (effect == 2) {
        color = float3(dot(color, float3(0.2126, 0.7152, 0.0722)));
    } else if (effect == 3) {
        const float edges[9] = { 1, 1, 1,   1, -8, 1,   1, 1, 1 };
        color = saturate(applyKernel(scene, s, in.uv, edges));
    }
    return float4(color, 1.0);
}
