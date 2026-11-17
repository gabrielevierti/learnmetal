# Transformations

So far objects sit wherever their vertices put them. To move, rotate and scale them without rewriting vertex buffers every frame, we multiply each vertex by a **matrix**. This chapter is a compact tour of the math, followed by a small Swift helper file used for the rest of the series.

## Vectors

A vector is a direction with a length. In graphics we also use vectors for positions (a direction from the origin) and colors. The operations that matter:

- **Addition and subtraction** work per component. `b - a` is the vector pointing from `a` to `b`.
- **Length**: `length(v)` is the square root of `x² + y² + z²`. A vector of length 1 is a **unit vector**, and `normalize(v)` scales any vector to length 1.
- **Dot product**: `dot(a, b) = a.x*b.x + a.y*b.y + a.z*b.z`. For unit vectors it equals the cosine of the angle between them: 1 when parallel, 0 when perpendicular, -1 when opposite. All of lighting is built on this.
- **Cross product**: `cross(a, b)` is a vector perpendicular to both inputs.

Swift's `simd` module provides all of these, with the same names as in MSL.

## Matrices

A 4×4 matrix can express any combination of scaling, rotation and translation. Multiplying a matrix by a vector applies the transformation.

**Scaling** puts the factors on the diagonal. **Translation** puts the offset in the last column, which is why we need four dimensions: a 3×3 matrix cannot move a point. The fourth component of a vector, **w**, switches translation on and off. Positions use `w = 1` and are moved; directions use `w = 0` and are not.

**Rotation** by an angle around an axis fills the upper-left 3×3 block with sines and cosines. You rarely write these by hand.

## Order matters

Matrix multiplication is not commutative. With column vectors, the convention in both Metal and `simd`, the matrix **closest to the vector applies first**:

```swift
let transform = translation * rotation * scale
// applied to a vertex: scale first, then rotate, then translate
```

Scale, then rotate, then translate is the order you almost always want. Translating first and rotating afterward swings the object around the origin like a stone on a string.

## A matrix helper

`simd` gives us the types but few constructors. Add `Math.swift`:

```swift
import simd

typealias Float3 = SIMD3<Float>

extension Float {
    var radians: Float { self * .pi / 180 }
}

extension float4x4 {
    static let identity = matrix_identity_float4x4

    init(translation t: Float3) {
        self = .identity
        columns.3 = SIMD4<Float>(t, 1)
    }

    init(scale s: Float3) {
        self.init(diagonal: SIMD4<Float>(s, 1))
    }

    init(rotation angle: Float, axis: Float3) {
        self.init(simd_quatf(angle: angle, axis: normalize(axis)))
    }

    /// The upper-left 3x3 part: rotation and scale without translation.
    var upperLeft: float3x3 {
        float3x3(SIMD3(columns.0.x, columns.0.y, columns.0.z),
                 SIMD3(columns.1.x, columns.1.y, columns.1.z),
                 SIMD3(columns.2.x, columns.2.y, columns.2.z))
    }
}
```

Angles are in radians everywhere; `45.radians` converts from degrees. Matrices are stored in **column-major** order: `columns.3` is the fourth column, where translation lives. MSL's `float4x4` uses the same layout, so a Swift matrix can be copied into a uniform buffer unchanged.

The rotation is built from a **quaternion**, a four-number representation of a rotation that is free of the gimbal lock problems that plague chained axis rotations. You do not need the theory to use it.

## Transforming the rectangle

Add a matrix to the uniforms and multiply in the vertex function:

```cpp
struct Uniforms {
    float4x4 transform;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant Uniforms &uniforms [[buffer(1)]]) {
    VertexOut out;
    out.position = uniforms.transform * float4(in.position, 1.0);
    out.uv = in.uv;
    return out;
}
```

The uniforms use vertex buffer slot **1** because slot 0 holds the vertex data. From here on that is our convention: slot 0 for vertices, slot 1 for uniforms.

```swift
struct Uniforms {
    var transform: float4x4
}

// in draw(in:)
let time = Float(CACurrentMediaTime() - startTime)
var uniforms = Uniforms(
    transform: float4x4(translation: [0.5, -0.5, 0])
             * float4x4(rotation: time, axis: [0, 0, 1])
             * float4x4(scale: [0.5, 0.5, 0.5]))
encoder.setVertexBytes(&uniforms, length: MemoryLayout<Uniforms>.stride, index: 1)
```

The rectangle is now half size, in the lower-right corner, spinning around its own center. If the window is not square it looks stretched while rotating. That is expected, and the projection matrix in the next chapter fixes it.

## Exercises

- Swap the translation and rotation and predict the result before running.
- Draw the rectangle a second time in the top-left corner with a scale that follows `sin(time)`. You only need a second `setVertexBytes` and a second draw call.
