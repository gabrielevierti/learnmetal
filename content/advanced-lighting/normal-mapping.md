# Normal Mapping

A brick wall rendered as a flat quad looks flat, however good the texture is. The lighting gives it away, because every fragment has the same normal. **Normal mapping** stores a different normal for every texel, so light reacts to bumps and grooves that are not there in the geometry.

## Normal maps

A normal is a vector with components from -1 to 1. Stored in an image, each component is remapped to the 0 to 1 range, and the shader undoes it:

```cpp
float3 normal = normalMap.sample(s, in.uv).xyz * 2.0 - 1.0;
```

Normal maps look bluish because most normals point straight out of the surface, along +z, which is stored as the color (0.5, 0.5, 1.0). Load normal maps as **linear** data, never sRGB.

## Tangent space

The normals in the map are expressed relative to the surface itself, in **tangent space**, where +z points away from the surface. That is what makes one map usable on a wall facing any direction, or wrapped around a curved model. To light with them, we need a way to rotate them from tangent space into world space.

That rotation is the **TBN matrix**, built from three perpendicular unit vectors at each vertex:

- **N**, the vertex normal,
- **T**, the **tangent**, pointing along the surface in the direction of increasing u,
- **B**, the **bitangent**, pointing along the surface in the direction of increasing v.

## Getting tangents

Tangents are computed from positions and texture coordinates. Model I/O does it for you. Add a tangent attribute to the vertex descriptor and ask for the basis after loading:

```swift
vertexDescriptor.attributes[3].format = .float3   // tangent
vertexDescriptor.attributes[3].offset = 32
vertexDescriptor.layouts[0].stride = 44

(mdlDescriptor.attributes[3] as! MDLVertexAttribute).name = MDLVertexAttributeTangent
```

```swift
mesh.addOrthTanBasis(forTextureCoordinateAttributeNamed: MDLVertexAttributeTextureCoordinate,
                     normalAttributeNamed: MDLVertexAttributeNormal,
                     tangentAttributeNamed: MDLVertexAttributeTangent)
mesh.vertexDescriptor = mdlDescriptor
```

Assigning the descriptor again makes Model I/O repack the buffers with the new attribute.

For hand-built geometry, the tangent of a triangle with edges `e1`, `e2` and texture coordinate differences `(du1, dv1)`, `(du2, dv2)` is:

```swift
let f = 1 / (du1 * dv2 - du2 * dv1)
let tangent = normalize(f * (dv2 * e1 - dv1 * e2))
```

## The shader

The vertex function transforms the normal and the tangent into world space:

```cpp
struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal   [[attribute(1)]];
    float2 uv       [[attribute(2)]];
    float3 tangent  [[attribute(3)]];
};

struct VertexOut {
    float4 position [[position]];
    float3 worldPosition;
    float3 normal;
    float3 tangent;
    float2 uv;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    float4 world = uniforms.model * float4(in.position, 1.0);
    out.position = uniforms.projection * uniforms.view * world;
    out.worldPosition = world.xyz;
    out.normal = uniforms.normalMatrix * in.normal;
    out.tangent = uniforms.normalMatrix * in.tangent;
    out.uv = in.uv;
    return out;
}
```

The fragment function rebuilds an exactly perpendicular basis, then rotates the sampled normal with it:

```cpp
static float3 perturbedNormal(VertexOut in, texture2d<float> normalMap, sampler s) {
    float3 N = normalize(in.normal);
    float3 T = normalize(in.tangent);
    T = normalize(T - dot(T, N) * N);     // Gram-Schmidt: make T perpendicular to N
    float3 B = cross(N, T);

    float3 tangentNormal = normalMap.sample(s, in.uv).xyz * 2.0 - 1.0;
    float3x3 TBN = float3x3(T, B, N);
    return normalize(TBN * tangentNormal);
}
```

`float3x3(T, B, N)` builds a matrix with those vectors as columns, so multiplying takes a tangent-space vector into world space. Use the returned normal in place of `normalize(in.normal)` everywhere in the lighting code. Nothing else changes.

## Green channel and handedness

Two things commonly make a normal-mapped surface look "inside out", with bumps lit as dents:

- **Normal map convention.** Maps come in two flavors that differ in the sign of the green channel, usually labeled OpenGL (+Y) and DirectX (-Y). Which one is right depends on which way your v coordinate and bitangent run. If bumps look inverted, negate `tangentNormal.y`.
- **Mirrored texture coordinates.** Symmetric models often mirror their UVs, which flips the bitangent on one half. Exporters encode this as a sign in the tangent's fourth component. Model I/O offers `addTangentBasis(forTextureCoordinateAttributeNamed:tangentAttributeNamed:bitangentAttributeNamed:)` to store an explicit bitangent if you need to support it.

A quick sanity check for any model: output `N * 0.5 + 0.5` as the color. Smoothly changing pastel colors mean the basis is healthy.

## Two-channel normal maps

Since a unit normal's z can be recomputed from x and y, normal maps are often stored with two channels in a compressed format, for example BC5 on Mac or EAC RG11 and ASTC on Apple GPUs:

```cpp
float2 xy = normalMap.sample(s, in.uv).rg * 2.0 - 1.0;
float3 tangentNormal = float3(xy, sqrt(saturate(1.0 - dot(xy, xy))));
```

## Exercises

- Rotate a normal-mapped quad over time and confirm the lighting stays consistent with a fixed light.
- Scale the x and y of the tangent normal by a "bump strength" uniform before normalizing.
