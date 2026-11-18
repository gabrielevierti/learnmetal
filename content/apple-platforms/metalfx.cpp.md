```cpp
#include <MetalFX/MetalFX.hpp>      // with MTLFX_PRIVATE_IMPLEMENTATION defined in one .cpp file

MTLFX::SpatialScalerDescriptor* descriptor = MTLFX::SpatialScalerDescriptor::alloc()->init();
descriptor->setInputWidth(renderWidth);
descriptor->setInputHeight(renderHeight);
descriptor->setOutputWidth(outputWidth);
descriptor->setOutputHeight(outputHeight);
descriptor->setColorTextureFormat(MTL::PixelFormatRGBA16Float);
descriptor->setOutputTextureFormat(MTL::PixelFormatRGBA16Float);
descriptor->setColorProcessingMode(MTLFX::SpatialScalerColorProcessingModeHDR);

MTLFX::SpatialScaler* scaler = descriptor->newSpatialScaler(device);
descriptor->release();
if (!scaler) {
    throw std::runtime_error("MetalFX spatial scaling is not supported on this device");
}
```

```cpp
scaler->setColorTexture(sceneTexture);
scaler->setOutputTexture(upscaledTexture);
scaler->encodeToCommandBuffer(commandBuffer);
```

```cpp
MTLFX::TemporalScalerDescriptor* descriptor = MTLFX::TemporalScalerDescriptor::alloc()->init();
descriptor->setInputWidth(renderWidth);
descriptor->setInputHeight(renderHeight);
descriptor->setOutputWidth(outputWidth);
descriptor->setOutputHeight(outputHeight);
descriptor->setColorTextureFormat(MTL::PixelFormatRGBA16Float);
descriptor->setDepthTextureFormat(MTL::PixelFormatDepth32Float);
descriptor->setMotionTextureFormat(MTL::PixelFormatRG16Float);
descriptor->setOutputTextureFormat(MTL::PixelFormatRGBA16Float);

MTLFX::TemporalScaler* scaler = descriptor->newTemporalScaler(device);
descriptor->release();
if (!scaler) {
    throw std::runtime_error("MetalFX temporal scaling is not supported on this device");
}
scaler->setMotionVectorScaleX(float(renderWidth));     // our vectors are in uv units; the scaler wants pixels
scaler->setMotionVectorScaleY(float(renderHeight));
```

```cpp
float halton(int index, int base) {
    float f = 1.0f, result = 0.0f;
    for (int i = index; i > 0; i /= base) {
        f /= float(base);
        result += f * float(i % base);
    }
    return result;
}

simd::float2 jitter = { halton(frameIndex % 8 + 1, 2) - 0.5f,
                        halton(frameIndex % 8 + 1, 3) - 0.5f };      // in pixels, -0.5 ... 0.5

// Shift clip space by that many pixels. Column 2 is multiplied by z, which cancels the divide by w.
simd::float4x4 jittered = projection;
jittered.columns[2].x += 2.0f * jitter.x / float(renderWidth);
jittered.columns[2].y -= 2.0f * jitter.y / float(renderHeight);
```

```cpp
scaler->setColorTexture(sceneTexture);
scaler->setDepthTexture(depthTexture);
scaler->setMotionTexture(motionTexture);
scaler->setOutputTexture(upscaledTexture);
scaler->setJitterOffsetX(jitter.x);
scaler->setJitterOffsetY(jitter.y);
scaler->setReset(cameraDidCut);                        // true for one frame after a teleport or scene change
scaler->encodeToCommandBuffer(commandBuffer);
```
