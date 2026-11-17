# Parallax Mapping

Normal mapping changes how a surface is lit, but not what you see where. At a shallow angle a normal-mapped brick wall still looks like a painted board, because the bricks do not hide the mortar behind them. **Parallax mapping** shifts the texture coordinates based on a height map and the viewing angle, so that high parts appear to cover low parts.

## The idea

Alongside the color and normal maps we need a **height map**, a grayscale texture describing the surface's relief. It is more convenient to store **depth**, the inverse of height: 0 at the top surface, 1 at the deepest point.

Picture the viewer looking at a point A on the flat polygon. On the real, bumpy surface, the line of sight would have hit the relief earlier, at some point B, and the viewer should see the texture at B. Parallax mapping estimates how far to slide the texture coordinate from A toward B.

All of this is done in **tangent space**, where the surface is the xy plane and the texture's u and v run along x and y. So the view direction must be converted into tangent space first.

## View direction in tangent space

The TBN matrix from the previous chapter converts tangent to world. Its transpose does the opposite, since the matrix is orthonormal:

```cpp
float3x3 TBN = float3x3(T, B, N);
float3 viewDirTangent = normalize(transpose(TBN) * (uniforms.viewPosition - in.worldPosition));
```

## Simple parallax mapping

Sample the depth at the current coordinate and move along the view direction by that amount:

```cpp
static float2 parallaxSimple(float2 uv, float3 viewDir,
                             texture2d<float> depthMap, sampler s, float scale) {
    float depth = depthMap.sample(s, uv).r;
    float2 offset = viewDir.xy / viewDir.z * (depth * scale);
    return uv - offset;
}
```

`scale` controls the strength; values around 0.05 to 0.1 are typical. The division by `viewDir.z` makes the shift larger at shallow angles. Then use the shifted coordinate for **every** texture lookup of the fragment: color, normal, specular.

```cpp
float2 uv = parallaxSimple(in.uv, viewDirTangent, depthMap, s, 0.1);
if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
    discard_fragment();
}
float3 albedo = diffuseMap.sample(s, uv).rgb;
float3 tangentNormal = normalMap.sample(s, uv).xyz * 2.0 - 1.0;
```

The discard trims the edges of a single quad, where shifted coordinates would leave the texture. On tiling surfaces you would leave it out.

!!! note "Sign conventions"
    Whether the offset is subtracted or added, and whether its y needs negating, depends on the direction of your v axis and bitangent. If the effect seems to bulge inward or slide the wrong way when you move the camera, flip the sign of the y component.

This one-sample version works for gentle relief. On steep height changes or at very low angles the estimate is poor and the surface seems to swim.

## Steep parallax mapping

A better estimate comes from marching along the view ray in small steps through a number of depth layers until the ray goes below the surface:

```cpp
static float2 parallaxSteep(float2 uv, float3 viewDir,
                            texture2d<float> depthMap, sampler s, float scale) {
    float layerCount = mix(32.0, 8.0, abs(viewDir.z));   // more layers at shallow angles
    float layerDepth = 1.0 / layerCount;
    float2 deltaUV = viewDir.xy / viewDir.z * scale / layerCount;

    float2 currentUV = uv;
    float currentLayerDepth = 0.0;
    float mapDepth = depthMap.sample(s, currentUV, level(0)).r;

    while (currentLayerDepth < mapDepth) {
        currentUV -= deltaUV;
        mapDepth = depthMap.sample(s, currentUV, level(0)).r;
        currentLayerDepth += layerDepth;
    }
    return currentUV;
}
```

Inside a loop the GPU cannot compute automatic mip levels reliably, so the samples name level 0 explicitly. The result is far more convincing, but the discrete layers show up as visible steps.

## Parallax occlusion mapping

The steps disappear if, instead of taking the first layer below the surface, we interpolate between the last point above the surface and the first one below it:

```cpp
    // ...after the loop in parallaxSteep
    float2 previousUV = currentUV + deltaUV;

    float afterDepth  = mapDepth - currentLayerDepth;
    float beforeDepth = depthMap.sample(s, previousUV, level(0)).r - currentLayerDepth + layerDepth;

    float weight = afterDepth / (afterDepth - beforeDepth);
    return mix(currentUV, previousUV, weight);
```

This is **parallax occlusion mapping** (POM). The two depths tell us how far each point is from the true surface, and a linear blend lands very close to the real intersection.

## Limits

- It is an illusion inside the polygon. The silhouette stays flat, and the effect breaks at glancing angles.
- It is expensive: dozens of texture reads per fragment. Reduce the layer count with distance.
- The relief casts no shadows on itself unless you march a second ray toward the light.

When you need real geometry, with real silhouettes and shadows, displace vertices using [tessellation](../beyond/tessellation.html).

## Exercises

- Switch between the three variants with a uniform and compare at a low viewing angle.
- Implement self-shadowing by marching from the found point toward the light in tangent space.
