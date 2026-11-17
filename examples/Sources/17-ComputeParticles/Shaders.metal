#include <metal_stdlib>
using namespace metal;

struct Particle {
    float3 position;
    float3 velocity;
    float life;
};

// ---------------------------------------------------------------- compute

struct SimulationUniforms {
    float3 attractor;
    float deltaTime;
    uint particleCount;
};

kernel void update_particles(device Particle *particles [[buffer(0)]],
                             constant SimulationUniforms &uniforms [[buffer(1)]],
                             uint id [[thread_position_in_grid]]) {
    // dispatchThreadgroups rounds the grid up, so skip threads past the end of the buffer.
    if (id >= uniforms.particleCount) { return; }

    Particle p = particles[id];

    float3 toAttractor = uniforms.attractor - p.position;
    float distanceSquared = max(dot(toAttractor, toAttractor), 0.25);
    float3 acceleration = normalize(toAttractor) * (6.0 / distanceSquared);

    p.velocity += acceleration * uniforms.deltaTime;
    p.velocity *= 0.999;                                // a little drag keeps the system stable
    p.position += p.velocity * uniforms.deltaTime;
    p.life = fract(p.life + uniforms.deltaTime * 0.1);

    particles[id] = p;      // each thread writes only its own element
}

// ---------------------------------------------------------------- render

struct DrawUniforms {
    float4x4 view;
    float4x4 projection;
    float size;
};

struct ParticleOut {
    float4 position [[position]];
    float2 corner;
    float3 color;
};

vertex ParticleOut vertex_particle(uint vertexID [[vertex_id]],
                                   uint instanceID [[instance_id]],
                                   const device Particle *particles [[buffer(0)]],
                                   constant DrawUniforms &uniforms [[buffer(1)]]) {
    const float2 corners[4] = { float2(-1, -1), float2(1, -1), float2(-1, 1), float2(1, 1) };
    Particle p = particles[instanceID];
    float2 corner = corners[vertexID];

    // Expand the quad in view space so it always faces the camera.
    float4 viewPosition = uniforms.view * float4(p.position, 1.0);
    viewPosition.xy += corner * uniforms.size;

    float speed = length(p.velocity);
    ParticleOut out;
    out.position = uniforms.projection * viewPosition;
    out.corner = corner;
    out.color = mix(float3(0.15, 0.35, 1.0), float3(1.0, 0.55, 0.15), saturate(speed * 0.25));
    return out;
}

fragment float4 fragment_particle(ParticleOut in [[stage_in]]) {
    // A soft round dot. With additive blending, overlapping particles add up to a glow.
    float falloff = saturate(1.0 - dot(in.corner, in.corner));
    return float4(in.color * falloff * 0.35, 1.0);
}
